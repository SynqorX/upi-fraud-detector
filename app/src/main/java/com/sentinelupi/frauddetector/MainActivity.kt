package com.sentinelupi.frauddetector

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ReceiptLong
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.engine.*
import com.sentinelupi.frauddetector.model.UpiTransactionRecord
import com.sentinelupi.frauddetector.network.LanP2PManager
import com.sentinelupi.frauddetector.network.LanPeer
import com.sentinelupi.frauddetector.network.P2pPaymentMessage
import com.sentinelupi.frauddetector.ui.components.AttackWarningDialog
import com.sentinelupi.frauddetector.ui.components.BalanceCustomizerDialog
import com.sentinelupi.frauddetector.ui.screens.PassbookScreen
import com.sentinelupi.frauddetector.ui.screens.SetupScreen
import com.sentinelupi.frauddetector.ui.screens.UpiHomeScreen
import com.sentinelupi.frauddetector.ui.theme.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.*

class MainActivity : ComponentActivity() {
    private var p2pManager: LanP2PManager? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            SentinelTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = PageBg
                ) {
                    SentinelUpiApp(
                        onRegisterP2pManager = { mgr -> p2pManager = mgr }
                    )
                }
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        p2pManager?.stopServer()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SentinelUpiApp(onRegisterP2pManager: (LanP2PManager) -> Unit) {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var activeTab by remember { mutableStateOf(0) }
    var accountBalance by remember { mutableStateOf(50000.0) } // Default ₹50,000, customizable!
    var showBalanceDialog by remember { mutableStateOf(false) }

    // User identity & device info
    var upiId by remember { mutableStateOf("supr@okaxis") }
    val deviceName = remember { "Android (${android.os.Build.MODEL})" }
    val localIp = remember { LanP2PManager.getLocalIpAddress() }

    // Active User Profile
    var profile by remember {
        mutableStateOf(
            UserProfile(
                userId = "USR_4091",
                ewmaMean = 1850.0,
                ewmaVar = 270400.0, // σ = 520.0
                trustedDevices = mutableMapOf("DEV_IN_SAMS23_001" to "Samsung Galaxy S23"),
                trustedCities = mutableListOf("Bengaluru"),
                lastCity = "Bengaluru",
                lastLat = 12.9716,
                lastLon = 77.5946
            )
        )
    }

    // P2P & Transaction History (Preloaded with sample records from preview.html)
    val transactionHistory = remember {
        mutableStateListOf(
            UpiTransactionRecord(
                id = "TXN_ATK_001",
                title = "Blocked: Rogue Drain",
                peerUpi = "unknown@darknet",
                amount = 75000.0,
                isDebit = true,
                status = "BLOCKED",
                riskScore = 99.4,
                riskTier = "CRITICAL",
                note = "03:15 AM • Cloud Emulator",
                explanation = EvaluationResult(
                    transactionId = "TXN_ATK_001",
                    riskScore = 99.4,
                    riskTier = "CRITICAL",
                    anomalyDiagnosis = "HOSTILE_ACCOUNT_TAKEOVER",
                    actionRecommendation = "CHALLENGE_BIOMETRIC_OR_BLOCK",
                    summaryNarrative = "A rogue nocturnal transfer of ₹75,000.00 was attempted at 03:15 AM from an unrecognized cloud emulator.",
                    factors = listOf(
                        RiskFactor("Spend Deviation", "CRITICAL", 40.0, "₹75,000.00 is 40.5x of user historical average."),
                        RiskFactor("Circadian Sleep Hours", "ELEVATED", 35.0, "Initiated during deep sleep window (01:00 AM - 05:30 AM IST)."),
                        RiskFactor("Untrusted Hardware", "CRITICAL", 40.0, "Unrecognized hardware fingerprint 'Linux Android Cloud Emulator'.")
                    ),
                    attributionBreakdown = mapOf("spend_deviation" to 40.0, "device_novelty" to 40.0, "temporal_anomaly" to 20.0)
                )
            ),
            UpiTransactionRecord(
                id = "TXN_LEGIT_002",
                title = "P2P to Rahul",
                peerUpi = "rahul@oksbi",
                amount = 500.0,
                isDebit = true,
                status = "SUCCESS",
                riskScore = 0.0,
                riskTier = "LOW",
                note = "Yesterday, 19:42"
            )
        )
    }

    // Discovered LAN peers
    val discoveredPeers = remember { mutableStateListOf<LanPeer>() }
    var isScanningPeers by remember { mutableStateOf(false) }

    // Attack Interception Alert State
    var showAttackAlert by remember { mutableStateOf(false) }
    var interceptedAttackResult by remember { mutableStateOf<EvaluationResult?>(null) }
    var interceptedAttackTxn by remember { mutableStateOf<TransactionInput?>(null) }

    // Initialize P2P Server once
    DisposableEffect(Unit) {
        val manager = LanP2PManager(deviceName = deviceName, upiId = upiId, port = 8989)
        onRegisterP2pManager(manager)

        manager.startServer(coroutineScope) { msg ->
            accountBalance += msg.amount
            val record = UpiTransactionRecord(
                id = msg.transactionId,
                title = "P2P from ${msg.senderUpi}",
                peerUpi = msg.senderUpi,
                amount = msg.amount,
                isDebit = false,
                status = "RECEIVED",
                riskScore = 0.0,
                riskTier = "LOW",
                note = msg.note
            )
            transactionHistory.add(0, record)
            Pair(true, "Received ₹${msg.amount} successfully by $upiId")
        }

        onDispose {
            manager.stopServer()
        }
    }

    Scaffold(
        containerColor = PageBg,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(
                            painter = painterResource(id = R.drawable.app_logo),
                            contentDescription = "SentinelUPI Logo",
                            modifier = Modifier
                                .size(34.dp)
                                .clip(RoundedCornerShape(10.dp))
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = "SentinelUPI",
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp,
                                color = InkDark
                            )
                            Text(
                                text = "$upiId • LAN $localIp",
                                fontSize = 10.sp,
                                color = InkMuted
                            )
                        }
                    }
                },
                actions = {
                    // Quick balance chip with customize trigger
                    Surface(
                        shape = RoundedCornerShape(20.dp),
                        color = Color.White,
                        border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                        shadowElevation = 0.5.dp,
                        modifier = Modifier
                            .padding(end = 8.dp)
                            .clickable { showBalanceDialog = true }
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                        ) {
                            Text(
                                text = "₹%,.0f".format(accountBalance),
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                color = MintPrimary
                            )
                            Spacer(modifier = Modifier.width(4.dp))
                            Icon(
                                Icons.Default.Edit,
                                contentDescription = "Edit Balance",
                                tint = SkyPrimary,
                                modifier = Modifier.size(11.dp)
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.White
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = Color.White,
                tonalElevation = 2.dp
            ) {
                val navColors = NavigationBarItemDefaults.colors(
                    selectedIconColor = MintPrimary,
                    selectedTextColor = MintPrimary,
                    indicatorColor = MintLight,
                    unselectedIconColor = InkSubtle,
                    unselectedTextColor = InkSubtle
                )
                NavigationBarItem(
                    selected = activeTab == 0,
                    onClick = { activeTab = 0 },
                    icon = { Icon(Icons.Default.Home, contentDescription = "Home") },
                    label = { Text("Home", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = navColors
                )
                NavigationBarItem(
                    selected = activeTab == 1,
                    onClick = { activeTab = 1 },
                    icon = { Icon(Icons.AutoMirrored.Filled.ReceiptLong, contentDescription = "History") },
                    label = { Text("History", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = navColors
                )
                NavigationBarItem(
                    selected = activeTab == 2,
                    onClick = { activeTab = 2 },
                    icon = { Icon(Icons.Default.Tune, contentDescription = "Setup") },
                    label = { Text("Setup", fontSize = 10.sp, fontWeight = FontWeight.Bold) },
                    colors = navColors
                )
            }
        }
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(PageBg)
        ) {
            when (activeTab) {
                0 -> UpiHomeScreen(
                    accountBalance = accountBalance,
                    localIp = localIp,
                    upiId = upiId,
                    discoveredPeers = discoveredPeers,
                    isScanningPeers = isScanningPeers,
                    onScanPeers = {
                        isScanningPeers = true
                        coroutineScope.launch {
                            val manager = LanP2PManager(deviceName, upiId)
                            val found = mutableListOf<LanPeer>()
                            val parts = localIp.split(".")
                            if (parts.size == 4) {
                                val prefix = "${parts[0]}.${parts[1]}.${parts[2]}"
                                val myLast = parts[3].toIntOrNull() ?: 1
                                listOf(myLast, 1, 2, 3, 100, 101, 102, 105).distinct().forEach { host ->
                                    val peer = manager.probePeer("$prefix.$host")
                                    if (peer != null) found.add(peer)
                                }
                            }
                            val selfPeer = manager.probePeer("127.0.0.1")
                            if (selfPeer != null && found.none { it.ip == selfPeer.ip }) found.add(selfPeer)

                            withContext(Dispatchers.Main) {
                                discoveredPeers.clear()
                                discoveredPeers.addAll(found)
                                isScanningPeers = false
                                Toast.makeText(context, "Scan complete: ${found.size} peer(s) found on LAN", Toast.LENGTH_SHORT).show()
                            }
                        }
                    },
                    onOpenBalanceDialog = { showBalanceDialog = true },
                    onSendPayment = { targetIp, targetUpi, amount, note ->
                        if (amount > accountBalance) {
                            Toast.makeText(context, "❌ Insufficient balance! (Current: ₹$accountBalance)", Toast.LENGTH_LONG).show()
                            return@UpiHomeScreen
                        }

                        // Evaluate transaction with SentinelUPI Engine
                        val txnInput = TransactionInput(
                            userId = profile.userId,
                            amount = amount,
                            category = MerchantCategory.P2P_Transfer,
                            deviceId = profile.trustedDevices.keys.firstOrNull() ?: "DEV_CURRENT",
                            deviceModel = profile.trustedDevices.values.firstOrNull() ?: "Android Phone",
                            locationCity = profile.trustedCities.firstOrNull() ?: "Bengaluru",
                            timestamp = Date(),
                            burstVelocity1h = 1
                        )
                        val feats = FeatureExtractor.extract(profile, txnInput)
                        val (riskScore, tier) = FraudClassifier.predictRisk(feats)
                        val eval = ExplainabilityEngine.generate(profile, txnInput, feats, riskScore, tier)

                        if (tier in listOf("HIGH", "CRITICAL")) {
                            // Intercepted as suspicious
                            interceptedAttackResult = eval
                            interceptedAttackTxn = txnInput
                            showAttackAlert = true
                            transactionHistory.add(0, UpiTransactionRecord(
                                id = txnInput.transactionId,
                                title = "Blocked: P2P to $targetUpi",
                                peerUpi = targetUpi,
                                amount = amount,
                                isDebit = true,
                                status = "BLOCKED",
                                riskScore = riskScore,
                                riskTier = tier,
                                note = note,
                                explanation = eval
                            ))
                        } else {
                            // Legitimate payment -> Execute P2P over LAN
                            coroutineScope.launch {
                                val p2pMsg = P2pPaymentMessage(
                                    transactionId = txnInput.transactionId,
                                    senderUpi = upiId,
                                    senderDevice = deviceName,
                                    senderCity = profile.trustedCities.firstOrNull() ?: "Bengaluru",
                                    amount = amount,
                                    note = note
                                )
                                val p2pMgr = LanP2PManager(deviceName, upiId)
                                val (ok, reply) = p2pMgr.sendPayment(targetIp, 8989, p2pMsg)

                                withContext(Dispatchers.Main) {
                                    if (ok) {
                                        accountBalance -= amount
                                        transactionHistory.add(0, UpiTransactionRecord(
                                            id = txnInput.transactionId,
                                            title = "P2P to $targetUpi",
                                            peerUpi = targetUpi,
                                            amount = amount,
                                            isDebit = true,
                                            status = "SUCCESS",
                                            riskScore = riskScore,
                                            riskTier = tier,
                                            note = note,
                                            explanation = eval
                                        ))
                                        Toast.makeText(context, "✅ Payment of ₹$amount sent successfully!", Toast.LENGTH_SHORT).show()
                                    } else {
                                        Toast.makeText(context, "LAN Transfer Status: $reply", Toast.LENGTH_LONG).show()
                                    }
                                }
                            }
                        }
                    },
                    onReceiveQrClick = {
                        Toast.makeText(context, "Receive QR code mode active", Toast.LENGTH_SHORT).show()
                    }
                )
                1 -> PassbookScreen(transactions = transactionHistory)
                2 -> SetupScreen(onCompleteSetup = { activeTab = 0 })
            }
        }

        // Balance Customization Modal Dialog
        if (showBalanceDialog) {
            BalanceCustomizerDialog(
                currentBalance = accountBalance,
                onDismiss = { showBalanceDialog = false },
                onSaveBalance = { newBal ->
                    accountBalance = newBal
                    showBalanceDialog = false
                    Toast.makeText(context, "Balance updated to ₹%,.2f".format(newBal), Toast.LENGTH_SHORT).show()
                }
            )
        }

        // Suspicious Attack Warning Modal (SHOWS WHY!)
        if (showAttackAlert && interceptedAttackResult != null) {
            AttackWarningDialog(
                result = interceptedAttackResult!!,
                txn = interceptedAttackTxn,
                onDismiss = { showAttackAlert = false }
            )
        }
    }
}
