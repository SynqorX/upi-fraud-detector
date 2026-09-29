package com.sentinelupi.frauddetector.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.sentinelupi.frauddetector.ui.theme.*

@Composable
fun BalanceCustomizerDialog(
    currentBalance: Double,
    onDismiss: () -> Unit,
    onSaveBalance: (Double) -> Unit
) {
    var editAmountText by remember { mutableStateOf("%.0f".format(currentBalance)) }

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            shape = RoundedCornerShape(28.dp),
            color = Color.White,
            border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorderSubtle),
            shadowElevation = 8.dp,
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .wrapContentHeight()
        ) {
            Column(modifier = Modifier.padding(22.dp)) {
                Text(
                    text = "Customize Balance",
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                    color = InkDark
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Set simulated UPI balance to test large transfers or fraud limit thresholds.",
                    fontSize = 11.sp,
                    color = InkMuted
                )
                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = editAmountText,
                    onValueChange = { editAmountText = it },
                    label = { Text("Available Balance (₹)", fontSize = 11.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
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

                Spacer(modifier = Modifier.height(14.dp))

                // Quick Increment Chips
                Text(
                    text = "QUICK ADJUSTMENTS",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    color = InkSubtle,
                    letterSpacing = 0.5.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    listOf(5000.0, 25000.0, 50000.0, 100000.0, 250000.0).forEach { preset ->
                        Surface(
                            shape = RoundedCornerShape(10.dp),
                            color = PageBg,
                            border = androidx.compose.foundation.BorderStroke(1.dp, InkBorder),
                            modifier = Modifier.clickable { editAmountText = "%.0f".format(preset) }
                        ) {
                            Text(
                                text = "₹%,.0f".format(preset),
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold,
                                color = InkDark
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(22.dp))

                // Action Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
                ) {
                    TextButton(onClick = onDismiss) {
                        Text("Cancel", color = InkMuted, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                    }

                    Button(
                        onClick = {
                            val newBal = editAmountText.toDoubleOrNull() ?: currentBalance
                            onSaveBalance(newBal)
                        },
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
                        contentPadding = PaddingValues()
                    ) {
                        Box(
                            modifier = Modifier
                                .background(
                                    Brush.horizontalGradient(listOf(MintPrimary, SkyPrimary)),
                                    shape = RoundedCornerShape(14.dp)
                                )
                                .padding(horizontal = 22.dp, vertical = 10.dp)
                        ) {
                            Text(
                                text = "Save Balance",
                                color = Color.White,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}
