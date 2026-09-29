package com.sentinelupi.frauddetector.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PhoneAndroid
import androidx.compose.material.icons.filled.QrCodeScanner
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.network.LanPeer
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun P2pTransferCard(
    localIp: String,
    discoveredPeers: List<LanPeer>,
    isScanningPeers: Boolean,
    onScanPeers: () -> Unit,
    onSendPayment: (String, String, Double, String) -> Unit
) {
    var targetIpText by remember { mutableStateOf(localIp) }
    var targetUpiText by remember { mutableStateOf("peer@okhdfc") }
    var amountText by remember { mutableStateOf("500") }
    var noteText by remember { mutableStateOf("Chai & Snacks") }

    Surface(
        shape = RoundedCornerShape(28.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
        shadowElevation = 1.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Header Row: Title & Peer Scan Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Default.Wifi,
                        contentDescription = null,
                        tint = SkyPrimary,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "Wi-Fi Peer Transfer",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = InkDark
                    )
                }

                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = SkyLight,
                    border = androidx.compose.foundation.BorderStroke(0.5.dp, SkyPrimary.copy(alpha = 0.3f)),
                    modifier = Modifier.clickable(enabled = !isScanningPeers) { onScanPeers() }
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(horizontal = 9.dp, vertical = 4.dp)
                    ) {
                        Icon(
                            Icons.Default.QrCodeScanner,
                            contentDescription = "Scan",
                            tint = SkyPrimary,
                            modifier = Modifier.size(12.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = if (isScanningPeers) "Scanning..." else "LAN $localIp",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = SkyPrimary,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Discovered Peers Row (if available)
            if (discoveredPeers.isNotEmpty()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    discoveredPeers.forEach { peer ->
                        val isSelected = targetIpText == peer.ip
                        Surface(
                            shape = RoundedCornerShape(14.dp),
                            color = if (isSelected) SkyLight else PageBg,
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (isSelected) SkyPrimary else InkBorder
                            ),
                            modifier = Modifier.clickable {
                                targetIpText = peer.ip
                                targetUpiText = peer.upiId
                            }
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    Icons.Default.PhoneAndroid,
                                    contentDescription = null,
                                    tint = if (isSelected) SkyPrimary else InkMuted,
                                    modifier = Modifier.size(14.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Column {
                                    Text(
                                        text = peer.deviceName,
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = InkDark
                                    )
                                    Text(
                                        text = peer.ip,
                                        fontSize = 10.sp,
                                        color = InkMuted,
                                        fontFamily = FontFamily.Monospace
                                    )
                                }
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(12.dp))
            }

            // Input 1: Receiver Device IP
            OutlinedTextField(
                value = targetIpText,
                onValueChange = { targetIpText = it },
                label = { Text("Receiver Device IP", fontSize = 11.sp) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(14.dp),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = SkyPrimary,
                    unfocusedBorderColor = InkBorder,
                    focusedContainerColor = Color.White,
                    unfocusedContainerColor = PageBg,
                    focusedLabelColor = SkyPrimary,
                    unfocusedLabelColor = InkMuted,
                    cursorColor = SkyPrimary
                )
            )

            Spacer(modifier = Modifier.height(10.dp))

            // Input 2: Amount & Pay Button in a clean row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = amountText,
                    onValueChange = { amountText = it },
                    label = { Text("Amount (₹)", fontSize = 11.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(14.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = MintPrimary,
                        unfocusedBorderColor = InkBorder,
                        focusedContainerColor = Color.White,
                        unfocusedContainerColor = PageBg,
                        focusedLabelColor = MintPrimary,
                        unfocusedLabelColor = InkMuted,
                        cursorColor = MintPrimary
                    )
                )

                // Minimal Gradient Pay Button
                Button(
                    onClick = {
                        val amt = amountText.toDoubleOrNull() ?: 0.0
                        if (amt > 0) {
                            onSendPayment(targetIpText.trim(), targetUpiText.trim(), amt, noteText.trim())
                        }
                    },
                    modifier = Modifier
                        .height(54.dp)
                        .padding(top = 6.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                    contentPadding = PaddingValues()
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxHeight()
                            .background(
                                Brush.horizontalGradient(listOf(MintPrimary, SkyPrimary)),
                                shape = RoundedCornerShape(14.dp)
                            )
                            .padding(horizontal = 24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Pay",
                            color = Color.White,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}
