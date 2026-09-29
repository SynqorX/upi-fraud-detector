package com.sentinelupi.frauddetector.network

import android.util.Log
import kotlinx.coroutines.*
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.PrintWriter
import java.net.*

data class LanPeer(
    val deviceName: String,
    val upiId: String,
    val ip: String,
    val port: Int = 8989
)

data class P2pPaymentMessage(
    val transactionId: String,
    val senderUpi: String,
    val senderDevice: String,
    val senderCity: String,
    val amount: Double,
    val note: String,
    val timestamp: Long = System.currentTimeMillis()
)

class LanP2PManager(
    private val deviceName: String,
    private val upiId: String,
    private val port: Int = 8989
) {
    private var serverSocket: ServerSocket? = null
    private var isRunning = false
    private var serverJob: Job? = null

    companion object {
        private const val TAG = "LanP2PManager"

        fun getLocalIpAddress(): String {
            try {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val networkInterface = interfaces.nextElement()
                    if (networkInterface.isLoopback || !networkInterface.isUp) continue
                    val addresses = networkInterface.inetAddresses
                    while (addresses.hasMoreElements()) {
                        val address = addresses.nextElement()
                        if (!address.isLoopbackAddress && address is Inet4Address) {
                            return address.hostAddress ?: "127.0.0.1"
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error determining local IP", e)
            }
            return "127.0.0.1"
        }
    }

    fun startServer(
        scope: CoroutineScope,
        onPaymentReceived: (P2pPaymentMessage) -> Pair<Boolean, String>
    ) {
        if (isRunning) return
        isRunning = true

        serverJob = scope.launch(Dispatchers.IO) {
            try {
                serverSocket = ServerSocket(port).apply {
                    reuseAddress = true
                }
                Log.i(TAG, "P2P Server listening on port $port")

                while (isActive && isRunning) {
                    try {
                        val client = serverSocket?.accept() ?: break
                        launch(Dispatchers.IO) {
                            handleClient(client, onPaymentReceived)
                        }
                    } catch (e: Exception) {
                        if (!isRunning) break
                        Log.e(TAG, "Accept error: ${e.message}")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Server socket initialization failed: ${e.message}")
            }
        }
    }

    private fun handleClient(
        socket: Socket,
        onPaymentReceived: (P2pPaymentMessage) -> Pair<Boolean, String>
    ) {
        try {
            socket.soTimeout = 8000
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))
            val writer = PrintWriter(socket.getOutputStream(), true)

            val rawMessage = reader.readLine()
            if (rawMessage.isNullOrBlank()) {
                socket.close()
                return
            }

            val json = JSONObject(rawMessage)
            val action = json.optString("action", "PAYMENT")

            if (action == "DISCOVER") {
                // Reply with our peer profile
                val resp = JSONObject().apply {
                    put("status", "OK")
                    put("deviceName", deviceName)
                    put("upiId", upiId)
                    put("ip", getLocalIpAddress())
                    put("port", port)
                }
                writer.println(resp.toString())
            } else if (action == "PAYMENT") {
                val p2pMsg = P2pPaymentMessage(
                    transactionId = json.optString("transactionId", "TXN_${System.currentTimeMillis()}"),
                    senderUpi = json.optString("senderUpi", "anonymous@upi"),
                    senderDevice = json.optString("senderDevice", "Unknown Device"),
                    senderCity = json.optString("senderCity", "Bengaluru"),
                    amount = json.optDouble("amount", 0.0),
                    note = json.optString("note", "P2P Transfer"),
                    timestamp = json.optLong("timestamp", System.currentTimeMillis())
                )

                val (success, message) = onPaymentReceived(p2pMsg)
                val resp = JSONObject().apply {
                    put("status", if (success) "SUCCESS" else "FAILED")
                    put("message", message)
                    put("receivedAmount", p2pMsg.amount)
                    put("receiverUpi", upiId)
                }
                writer.println(resp.toString())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error handling client packet: ${e.message}")
        } finally {
            try { socket.close() } catch (_: Exception) {}
        }
    }

    suspend fun sendPayment(
        targetIp: String,
        targetPort: Int = 8989,
        payment: P2pPaymentMessage
    ): Pair<Boolean, String> = withContext(Dispatchers.IO) {
        var socket: Socket? = null
        try {
            socket = Socket()
            socket.connect(InetSocketAddress(targetIp, targetPort), 4000)
            socket.soTimeout = 6000

            val writer = PrintWriter(socket.getOutputStream(), true)
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))

            val payload = JSONObject().apply {
                put("action", "PAYMENT")
                put("transactionId", payment.transactionId)
                put("senderUpi", payment.senderUpi)
                put("senderDevice", payment.senderDevice)
                put("senderCity", payment.senderCity)
                put("amount", payment.amount)
                put("note", payment.note)
                put("timestamp", payment.timestamp)
            }

            writer.println(payload.toString())

            val rawResponse = reader.readLine()
            if (rawResponse.isNullOrBlank()) {
                return@withContext Pair(false, "No response from receiver device at $targetIp:$targetPort")
            }

            val respJson = JSONObject(rawResponse)
            val status = respJson.optString("status", "FAILED")
            val message = respJson.optString("message", "Payment processed")

            if (status == "SUCCESS") {
                Pair(true, message)
            } else {
                Pair(false, "Receiver declined payment: $message")
            }
        } catch (e: ConnectException) {
            Pair(false, "Could not connect to peer at $targetIp:$targetPort. Is the app open on the peer device?")
        } catch (e: SocketTimeoutException) {
            Pair(false, "Connection timed out connecting to $targetIp:$targetPort.")
        } catch (e: Exception) {
            Pair(false, "Payment network error: ${e.localizedMessage ?: e.message}")
        } finally {
            try { socket?.close() } catch (_: Exception) {}
        }
    }

    suspend fun probePeer(targetIp: String, targetPort: Int = 8989): LanPeer? = withContext(Dispatchers.IO) {
        var socket: Socket? = null
        try {
            socket = Socket()
            socket.connect(InetSocketAddress(targetIp, targetPort), 1500)
            socket.soTimeout = 2000

            val writer = PrintWriter(socket.getOutputStream(), true)
            val reader = BufferedReader(InputStreamReader(socket.getInputStream()))

            val payload = JSONObject().apply {
                put("action", "DISCOVER")
            }
            writer.println(payload.toString())

            val rawResponse = reader.readLine() ?: return@withContext null
            val respJson = JSONObject(rawResponse)
            if (respJson.optString("status") == "OK") {
                return@withContext LanPeer(
                    deviceName = respJson.optString("deviceName", "Peer Device"),
                    upiId = respJson.optString("upiId", "peer@upi"),
                    ip = targetIp,
                    port = targetPort
                )
            }
        } catch (_: Exception) {
            // Peer not responding or offline
        } finally {
            try { socket?.close() } catch (_: Exception) {}
        }
        null
    }

    fun stopServer() {
        isRunning = false
        serverJob?.cancel()
        try {
            serverSocket?.close()
        } catch (e: Exception) {
            Log.e(TAG, "Error closing server socket", e)
        }
    }
}
