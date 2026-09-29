package com.sentinelupi.frauddetector.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun HeroBalanceCard(
    balance: Double,
    upiId: String,
    localIp: String,
    onEditBalanceClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(32.dp),
        color = Color.White,
        border = androidx.compose.foundation.BorderStroke(1.5.dp, GlassBorder),
        shadowElevation = 2.dp,
        modifier = Modifier.fillMaxWidth()
    ) {
        Box(
            modifier = Modifier
                .background(
                    Brush.linearGradient(
                        colors = listOf(
                            CardHeroGradStart,
                            CardHeroGradMid,
                            CardHeroGradEnd
                        )
                    )
                )
                .padding(24.dp)
        ) {
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Available Balance",
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Medium,
                    color = InkMuted
                )
                Spacer(modifier = Modifier.height(6.dp))

                Row(
                    verticalAlignment = Alignment.Bottom,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = "₹",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        color = MintPrimary
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "%,.2f".format(balance),
                        fontSize = 38.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = InkDark,
                        letterSpacing = (-0.5).sp
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Minimalist Edit Balance Pill Button
                Surface(
                    shape = RoundedCornerShape(20.dp),
                    color = Color.White,
                    border = androidx.compose.foundation.BorderStroke(1.dp, InkBorder),
                    shadowElevation = 0.5.dp,
                    modifier = Modifier.clickable { onEditBalanceClick() }
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Icon(
                            Icons.Default.Edit,
                            contentDescription = "Edit Balance",
                            tint = SkyPrimary,
                            modifier = Modifier.size(12.dp)
                        )
                        Spacer(modifier = Modifier.width(5.dp))
                        Text(
                            text = "Edit Balance",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = SkyPrimary
                        )
                    }
                }
            }
        }
    }
}
