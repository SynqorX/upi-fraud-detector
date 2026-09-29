package com.sentinelupi.frauddetector.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowOutward
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.network.LanPeer
import com.sentinelupi.frauddetector.ui.components.HeroBalanceCard
import com.sentinelupi.frauddetector.ui.components.P2pTransferCard
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun UpiHomeScreen(
    accountBalance: Double,
    localIp: String,
    upiId: String,
    discoveredPeers: List<LanPeer>,
    isScanningPeers: Boolean,
    onScanPeers: () -> Unit,
    onOpenBalanceDialog: () -> Unit,
    onSendPayment: (String, String, Double, String) -> Unit,
    onReceiveQrClick: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PageBg)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            // Top Subtle Identity Bar
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "PERSONAL ACCOUNT",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = InkSubtle,
                        letterSpacing = 0.8.sp
                    )
                    Text(
                        text = "State Bank of India",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        color = InkDark
                    )
                }

                // Protected Badge Glass Pill
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = Color.White,
                    border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                    shadowElevation = 0.5.dp
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(MintPrimary)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "PROTECTED",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = MintPrimary,
                            letterSpacing = 0.5.sp
                        )
                    }
                }
            }

            // 1. Hero Floating Frosted Glass Balance Card
            HeroBalanceCard(
                balance = accountBalance,
                upiId = upiId,
                localIp = localIp,
                onEditBalanceClick = onOpenBalanceDialog
            )

            Spacer(modifier = Modifier.height(20.dp))

            // 2. Two Minimal Action Pills (Send Money & Receive QR)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(14.dp)
            ) {
                // Pill 1: Send Money
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = Color.White,
                    border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                    shadowElevation = 1.dp,
                    modifier = Modifier
                        .weight(1f)
                        .clickable { /* focus or scroll to p2p */ }
                ) {
                    Column(
                        modifier = Modifier.padding(vertical = 16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = SkyLight,
                            modifier = Modifier.size(42.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Default.ArrowOutward,
                                    contentDescription = "Send Money",
                                    tint = SkyPrimary,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Send Money",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = InkDark
                        )
                    }
                }

                // Pill 2: Receive QR
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = Color.White,
                    border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                    shadowElevation = 1.dp,
                    modifier = Modifier
                        .weight(1f)
                        .clickable { onReceiveQrClick() }
                ) {
                    Column(
                        modifier = Modifier.padding(vertical = 16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Surface(
                            shape = CircleShape,
                            color = MintLight,
                            modifier = Modifier.size(42.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Default.QrCode,
                                    contentDescription = "Receive QR",
                                    tint = MintPrimary,
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Receive QR",
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            color = InkDark
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // 3. P2P Quick Send Section (Airy, Minimalist)
            P2pTransferCard(
                localIp = localIp,
                discoveredPeers = discoveredPeers,
                isScanningPeers = isScanningPeers,
                onScanPeers = onScanPeers,
                onSendPayment = onSendPayment
            )
        }

        // Quiet Bottom State Indicator
        Spacer(modifier = Modifier.height(24.dp))
        Text(
            text = "Sentinel Engine Active • Offline Behavioral Shield",
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
            color = InkSubtle,
            modifier = Modifier
                .align(Alignment.CenterHorizontally)
                .padding(bottom = 8.dp)
        )
    }
}
