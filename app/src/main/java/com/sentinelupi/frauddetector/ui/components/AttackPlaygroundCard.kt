package com.sentinelupi.frauddetector.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun AttackPlaygroundCard(onSimulateAttack: (Int) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .border(
                1.5.dp,
                Brush.horizontalGradient(
                    listOf(OrangePrimary.copy(alpha = 0.8f), GoldPrimary.copy(alpha = 0.5f))
                ),
                RoundedCornerShape(20.dp)
            ),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        shape = RoundedCornerShape(20.dp)
    ) {
        Box(
            modifier = Modifier
                .background(
                    Brush.verticalGradient(
                        colors = listOf(AttackGradientStart, AttackGradientEnd)
                    )
                )
                .padding(18.dp)
        ) {
            Column {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.WarningAmber,
                            contentDescription = null,
                            tint = OrangePrimary,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Threat Simulation Lab",
                            fontFamily = FontFamily.Serif,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = GoldLight
                        )
                    }

                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        color = OrangePrimary.copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, GoldPrimary.copy(alpha = 0.5f))
                    ) {
                        Text(
                            text = "TEST DEFENSE",
                            fontFamily = FontFamily.Serif,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.ExtraBold,
                            color = GoldLight,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Launch an unauthorized cyber attack to verify SentinelUPI's multi-vector threat interception.",
                    fontFamily = FontFamily.Serif,
                    fontSize = 12.sp,
                    color = TextSecondary,
                    lineHeight = 16.sp
                )

                Spacer(modifier = Modifier.height(14.dp))

                // Attack Item 1: 3:15 AM Rogue Emulator
                AttackTriggerRow(
                    title = "🚨 3:15 AM Rogue Emulator Cashout",
                    subtitle = "₹75,000 P2P • Linux Cloud Emulator • Circadian Sleep Hours",
                    accentColor = RiskCritical,
                    onClick = { onSimulateAttack(1) }
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Attack Item 2: Hypersonic Moscow Geo-Jump
                AttackTriggerRow(
                    title = "⚡ Hypersonic Geo-Jump (Moscow in 15m)",
                    subtitle = "₹32,000 P2P • 23,000 km/h Implied Velocity • Foreign Device",
                    accentColor = OrangePrimary,
                    onClick = { onSimulateAttack(2) }
                )

                Spacer(modifier = Modifier.height(8.dp))

                // Attack Item 3: Botnet Micro-Carding
                AttackTriggerRow(
                    title = "🤖 Botnet Micro-Carding Burst",
                    subtitle = "15 rapid micro-transactions / 2m • Automated Drain Script",
                    accentColor = GoldPrimary,
                    onClick = { onSimulateAttack(3) }
                )
            }
        }
    }
}

@Composable
fun AttackTriggerRow(
    title: String,
    subtitle: String,
    accentColor: Color,
    onClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(12.dp),
        color = DarkSurface.copy(alpha = 0.9f),
        border = androidx.compose.foundation.BorderStroke(1.dp, accentColor.copy(alpha = 0.5f)),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() }
    ) {
        Row(
            modifier = Modifier.padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    fontFamily = FontFamily.Serif,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = subtitle,
                    fontFamily = FontFamily.Serif,
                    fontSize = 10.sp,
                    color = TextSecondary
                )
            }

            Surface(
                shape = CircleShape,
                color = accentColor.copy(alpha = 0.15f),
                modifier = Modifier.size(28.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = "Simulate",
                        tint = accentColor,
                        modifier = Modifier.size(14.dp)
                    )
                }
            }
        }
    }
}
