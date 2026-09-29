package com.sentinelupi.frauddetector.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.sentinelupi.frauddetector.engine.EvaluationResult
import com.sentinelupi.frauddetector.engine.TransactionInput
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun AttackWarningDialog(
    result: EvaluationResult,
    txn: TransactionInput?,
    onDismiss: () -> Unit
) {
    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            shape = RoundedCornerShape(32.dp),
            color = Color.White,
            border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
            shadowElevation = 8.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .wrapContentHeight()
                .padding(16.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                // Top Header: Shield Icon & Title
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(bottom = 18.dp)
                ) {
                    Surface(
                        shape = RoundedCornerShape(16.dp),
                        color = RiskCriticalLight,
                        border = androidx.compose.foundation.BorderStroke(1.dp, RiskCriticalBorder),
                        modifier = Modifier.size(48.dp)
                    ) {
                        Box(contentAlignment = Alignment.Center) {
                            Icon(
                                Icons.Default.Shield,
                                contentDescription = "Alert",
                                tint = RiskCritical,
                                modifier = Modifier.size(24.dp)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.width(14.dp))
                    Column {
                        Text(
                            text = "PROTECTION ALERT",
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            color = RiskCritical,
                            letterSpacing = 1.sp
                        )
                        Text(
                            text = "Attack Intercepted",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold,
                            color = InkDark
                        )
                    }
                }

                // Threat Score Box (Red Tinted Light Glass)
                Surface(
                    shape = RoundedCornerShape(18.dp),
                    color = RiskCriticalLight.copy(alpha = 0.6f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, RiskCriticalBorder),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 16.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "Anomaly Threat Score",
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Medium,
                                color = RiskCritical
                            )
                            Row(verticalAlignment = Alignment.Bottom) {
                                Text(
                                    text = "%.1f".format(result.riskScore),
                                    fontSize = 26.sp,
                                    fontWeight = FontWeight.ExtraBold,
                                    color = RiskCritical
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(
                                    text = "/ 100",
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    color = RiskCritical.copy(alpha = 0.7f)
                                )
                            }
                        }

                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = RiskCritical.copy(alpha = 0.15f),
                            border = androidx.compose.foundation.BorderStroke(0.5.dp, RiskCritical.copy(alpha = 0.4f))
                        ) {
                            Text(
                                text = result.riskTier + " BLOCK",
                                color = RiskCritical,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 5.dp)
                            )
                        }
                    }
                }

                // Narrative Summary
                Text(
                    text = result.summaryNarrative,
                    fontSize = 12.sp,
                    color = InkMuted,
                    lineHeight = 18.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )

                // Factors Breakdown
                if (result.factors.isNotEmpty()) {
                    Column(
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.padding(bottom = 20.dp)
                    ) {
                        result.factors.take(3).forEach { factor ->
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = PageBg,
                                border = androidx.compose.foundation.BorderStroke(1.dp, InkBorder),
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(horizontal = 12.dp, vertical = 10.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = factor.title,
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.SemiBold,
                                        color = InkDark
                                    )
                                    Text(
                                        text = "+%.0f".format(factor.contributionPercent),
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = if (factor.contributionPercent > 0) RiskCritical else MintPrimary
                                    )
                                }
                            }
                        }
                    }
                }

                // Dismiss Button
                Button(
                    onClick = onDismiss,
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = InkDark),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                ) {
                    Text(
                        text = "Dismiss & Secure Account",
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}
