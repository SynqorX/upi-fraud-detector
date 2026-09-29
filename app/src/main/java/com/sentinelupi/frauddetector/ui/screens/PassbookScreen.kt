package com.sentinelupi.frauddetector.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.CallReceived
import androidx.compose.material.icons.filled.ReceiptLong
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.model.UpiTransactionRecord
import com.sentinelupi.frauddetector.ui.components.AttackWarningDialog
import com.sentinelupi.frauddetector.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

@Composable
fun PassbookScreen(transactions: List<UpiTransactionRecord>) {
    val sdf = remember { SimpleDateFormat("dd MMM, HH:mm", Locale.getDefault()) }
    var selectedRecordForDetails by remember { mutableStateOf<UpiTransactionRecord?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PageBg)
            .padding(horizontal = 20.dp, vertical = 16.dp)
    ) {
        // Top Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "Recent Activity",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = InkDark
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Verified transfers & security blocks",
                    fontSize = 11.sp,
                    color = InkMuted
                )
            }

            Surface(
                shape = RoundedCornerShape(12.dp),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, InkBorder)
            ) {
                Text(
                    text = "${transactions.size} Records",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = InkMuted,
                    modifier = Modifier.padding(horizontal = 9.dp, vertical = 4.dp)
                )
            }
        }

        if (transactions.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(32.dp),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Surface(
                        shape = CircleShape,
                        color = SkyLight,
                        modifier = Modifier.size(56.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                Icons.Default.ReceiptLong,
                                contentDescription = null,
                                tint = SkyPrimary,
                                modifier = Modifier.size(26.dp)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(14.dp))
                    Text(
                        text = "No transactions recorded yet.",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        color = InkMuted
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(transactions) { txn ->
                    val isBlocked = txn.status == "BLOCKED"
                    val isReceived = txn.status == "RECEIVED"

                    Surface(
                        shape = RoundedCornerShape(20.dp),
                        color = Color.White,
                        border = androidx.compose.foundation.BorderStroke(
                            1.dp,
                            if (isBlocked) RiskCritical.copy(alpha = 0.35f) else GlassBorderSubtle
                        ),
                        shadowElevation = 0.5.dp,
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                if (isBlocked && txn.explanation != null) {
                                    selectedRecordForDetails = txn
                                }
                            }
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(14.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Icon according to status
                            Surface(
                                shape = RoundedCornerShape(14.dp),
                                color = when {
                                    isBlocked -> RiskCriticalLight
                                    isReceived -> MintLight
                                    else -> SkyLight
                                },
                                modifier = Modifier.size(40.dp)
                            ) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        when {
                                            isBlocked -> Icons.Default.Shield
                                            isReceived -> Icons.Default.CallReceived
                                            else -> Icons.AutoMirrored.Filled.ArrowForward
                                        },
                                        contentDescription = null,
                                        tint = when {
                                            isBlocked -> RiskCritical
                                            isReceived -> MintPrimary
                                            else -> SkyPrimary
                                        },
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            }

                            Spacer(modifier = Modifier.width(12.dp))

                            // Details
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = txn.title,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = InkDark
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    text = "${txn.peerUpi} • ${sdf.format(Date(txn.timestamp))}",
                                    fontSize = 11.sp,
                                    color = InkMuted
                                )
                                if (isBlocked) {
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        text = "Tap to view intercept details",
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = RiskCritical
                                    )
                                }
                            }

                            // Amount & Status
                            Column(horizontalAlignment = Alignment.End) {
                                val prefix = when {
                                    isBlocked -> "₹"
                                    isReceived -> "+₹"
                                    else -> "-₹"
                                }
                                Text(
                                    text = "$prefix%,.2f".format(txn.amount),
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = if (isBlocked) RiskCritical else InkDark
                                )
                                Spacer(modifier = Modifier.height(3.dp))
                                Surface(
                                    shape = RoundedCornerShape(6.dp),
                                    color = when {
                                        isBlocked -> RiskCriticalLight
                                        isReceived -> MintLight
                                        else -> SkyLight
                                    }
                                ) {
                                    Text(
                                        text = if (isBlocked) "BLOCKED" else "VERIFIED",
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                                        fontSize = 9.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = when {
                                            isBlocked -> RiskCritical
                                            isReceived -> MintPrimary
                                            else -> SkyPrimary
                                        }
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Modal to re-examine blocked transaction
    selectedRecordForDetails?.explanation?.let { eval ->
        AttackWarningDialog(
            result = eval,
            txn = null,
            onDismiss = { selectedRecordForDetails = null }
        )
    }
}
