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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Security
import androidx.compose.material3.*
import androidx.compose.runtime.*
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
fun SetupScreen(
    onCompleteSetup: () -> Unit
) {
    var phoneNumber by remember { mutableStateOf("98765 43210") }
    var locationPermissionGranted by remember { mutableStateOf(true) }
    var hardwarePermissionGranted by remember { mutableStateOf(true) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(PageBg)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 24.dp, vertical = 20.dp),
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        Column {
            // Minimal Step Indicator & Back Pill
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 28.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = CircleShape,
                    color = Color.White,
                    border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                    modifier = Modifier
                        .size(36.dp)
                        .clickable { onCompleteSetup() }
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = InkMuted,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }

                Surface(
                    shape = RoundedCornerShape(12.dp),
                    color = SkyLight,
                    border = androidx.compose.foundation.BorderStroke(0.5.dp, SkyPrimary.copy(alpha = 0.3f))
                ) {
                    Text(
                        text = "1 of 2",
                        color = SkyPrimary,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                    )
                }
            }

            // Hero Setup Title
            Text(
                text = "Welcome to\nSentinelUPI",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = InkDark,
                lineHeight = 34.sp
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Airy, zero-cloud peer payments protected by offline behavioral fraud intelligence.",
                fontSize = 13.sp,
                color = InkMuted,
                lineHeight = 18.sp
            )

            Spacer(modifier = Modifier.height(28.dp))

            // Phone Number Input Card
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                shadowElevation = 1.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "MOBILE NUMBER",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = InkSubtle,
                        letterSpacing = 0.8.sp
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(PageBg, RoundedCornerShape(12.dp))
                            .border(1.dp, InkBorder, RoundedCornerShape(12.dp))
                            .padding(horizontal = 12.dp, vertical = 10.dp)
                    ) {
                        Text(
                            text = "+91",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = MintPrimary
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = phoneNumber,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.SemiBold,
                            color = InkDark,
                            modifier = Modifier.weight(1f)
                        )
                        Icon(
                            Icons.Default.Check,
                            contentDescription = "Verified",
                            tint = MintPrimary,
                            modifier = Modifier.size(16.dp)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Required Protections Checklist
            Text(
                text = "REQUIRED PROTECTIONS",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = InkSubtle,
                letterSpacing = 0.8.sp
            )
            Spacer(modifier = Modifier.height(10.dp))

            // Permission 1: Geo-Velocity
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                shadowElevation = 1.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = SkyLight,
                            modifier = Modifier.size(38.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Default.LocationOn,
                                    contentDescription = "Location",
                                    tint = SkyPrimary,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "Location Velocity",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = InkDark
                            )
                            Text(
                                text = "Blocks impossible travel jumps",
                                fontSize = 11.sp,
                                color = InkMuted
                            )
                        }
                    }
                    Switch(
                        checked = locationPermissionGranted,
                        onCheckedChange = { locationPermissionGranted = it },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = MintPrimary,
                            uncheckedThumbColor = InkMuted,
                            uncheckedTrackColor = InkBorder
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Permission 2: Hardware Signature
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = Color.White,
                border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
                shadowElevation = 1.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = MintLight,
                            modifier = Modifier.size(38.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Default.Security,
                                    contentDescription = "Hardware",
                                    tint = MintPrimary,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "Hardware Signature",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = InkDark
                            )
                            Text(
                                text = "Identifies untrusted rogue emulators",
                                fontSize = 11.sp,
                                color = InkMuted
                            )
                        }
                    }
                    Switch(
                        checked = hardwarePermissionGranted,
                        onCheckedChange = { hardwarePermissionGranted = it },
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = Color.White,
                            checkedTrackColor = MintPrimary,
                            uncheckedThumbColor = InkMuted,
                            uncheckedTrackColor = InkBorder
                        )
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Authorize & Enter Primary Action Button
        Button(
            onClick = { onCompleteSetup() },
            modifier = Modifier
                .fillMaxWidth()
                .height(54.dp),
            shape = RoundedCornerShape(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
            contentPadding = PaddingValues()
        ) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(
                        Brush.horizontalGradient(listOf(MintPrimary, SkyPrimary)),
                        shape = RoundedCornerShape(16.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = "Authorize & Enter",
                        color = Color.White,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Icon(
                        Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }
    }
}
