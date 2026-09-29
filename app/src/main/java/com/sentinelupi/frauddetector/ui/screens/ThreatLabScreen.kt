package com.sentinelupi.frauddetector.ui.screens

import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.sentinelupi.frauddetector.engine.*
import com.sentinelupi.frauddetector.ui.theme.*
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ThreatLabScreen(profile: UserProfile) {
    var amountText by remember { mutableStateOf("18500") }
    var selectedCategory by remember { mutableStateOf(MerchantCategory.Electronics_Gadgets) }
    var selectedCity by remember { mutableStateOf("Bengaluru") }
    var deviceIdText by remember { mutableStateOf(profile.trustedDevices.keys.firstOrNull() ?: "DEV_IN_SAMS23_001") }
    var deviceModelText by remember { mutableStateOf(profile.trustedDevices.values.firstOrNull() ?: "Samsung Galaxy S23") }
    var hourIST by remember { mutableStateOf(19) }
    var burstCount by remember { mutableStateOf(1) }

    var latestResult by remember { mutableStateOf<EvaluationResult?>(null) }
    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp)
    ) {
        Text(
            text = "⚡ Fraud Engine Condition Inspector",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = TextPrimary
        )
        Text(
            text = "Inspect multi-vector behavioral deviation features without blind alerts.",
            fontSize = 11.sp,
            color = TextSecondary
        )
        Spacer(modifier = Modifier.height(12.dp))

        // Preset Scenario Chips
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            PresetChip("🛒 Routine Chai (₹280)") {
                amountText = "280"
                selectedCategory = MerchantCategory.Groceries_Daily
                selectedCity = profile.trustedCities.first()
                deviceIdText = profile.trustedDevices.keys.first()
                deviceModelText = profile.trustedDevices.values.first()
                hourIST = 14
                burstCount = 1
            }
            PresetChip("✨ Festive Spike (₹18,500)") {
                amountText = "18500"
                selectedCategory = MerchantCategory.Electronics_Gadgets
                selectedCity = profile.trustedCities.first()
                deviceIdText = profile.trustedDevices.keys.first()
                deviceModelText = profile.trustedDevices.values.first()
                hourIST = 19
                burstCount = 1
            }
            PresetChip("✈️ Goa Travel (₹4,200)") {
                amountText = "4200"
                selectedCategory = MerchantCategory.Food_Dining
                selectedCity = "Goa"
                deviceIdText = profile.trustedDevices.keys.first()
                deviceModelText = profile.trustedDevices.values.first()
                hourIST = 20
                burstCount = 1
            }
            PresetChip("🚨 Hostile Takeover (₹75k)") {
                amountText = "75000"
                selectedCategory = MerchantCategory.P2P_Transfer
                selectedCity = "Bengaluru"
                deviceIdText = "DEV_ROGUE_EMULATOR_99"
                deviceModelText = "Linux Cloud Emulator"
                hourIST = 3
                burstCount = 3
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Input Form Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, DarkSurfaceBorder, RoundedCornerShape(16.dp)),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                OutlinedTextField(
                    value = amountText,
                    onValueChange = { amountText = it },
                    label = { Text("Transaction Amount (INR ₹)") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(10.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = EmeraldGreen,
                        unfocusedBorderColor = DarkSurfaceBorder
                    )
                )

                Spacer(modifier = Modifier.height(8.dp))

                var catExpanded by remember { mutableStateOf(false) }
                ExposedDropdownMenuBox(
                    expanded = catExpanded,
                    onExpandedChange = { catExpanded = !catExpanded }
                ) {
                    OutlinedTextField(
                        value = selectedCategory.displayName,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Merchant Category") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = catExpanded) },
                        modifier = Modifier.fillMaxWidth().menuAnchor(),
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = EmeraldGreen,
                            unfocusedBorderColor = DarkSurfaceBorder
                        )
                    )
                    ExposedDropdownMenu(
                        expanded = catExpanded,
                        onDismissRequest = { catExpanded = false }
                    ) {
                        MerchantCategory.values().forEach { cat ->
                            DropdownMenuItem(
                                text = { Text(cat.displayName) },
                                onClick = {
                                    selectedCategory = cat
                                    catExpanded = false
                                }
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = deviceModelText,
                        onValueChange = { deviceModelText = it },
                        label = { Text("Device Model") },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = EmeraldGreen,
                            unfocusedBorderColor = DarkSurfaceBorder
                        )
                    )
                    OutlinedTextField(
                        value = selectedCity,
                        onValueChange = { selectedCity = it },
                        label = { Text("City") },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(10.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = EmeraldGreen,
                            unfocusedBorderColor = DarkSurfaceBorder
                        )
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(text = "Hour: $hourIST:00 IST", fontSize = 11.sp, color = TextSecondary)
                        Slider(
                            value = hourIST.toFloat(),
                            onValueChange = { hourIST = it.toInt() },
                            valueRange = 0f..23f,
                            colors = SliderDefaults.colors(thumbColor = EmeraldGreen, activeTrackColor = EmeraldGreen)
                        )
                    }
                    Column(modifier = Modifier.weight(1f)) {
                        Text(text = "Burst: $burstCount txn/h", fontFamily = androidx.compose.ui.text.font.FontFamily.Serif, fontSize = 11.sp, color = TextSecondary)
                        Slider(
                            value = burstCount.toFloat(),
                            onValueChange = { burstCount = it.toInt() },
                            valueRange = 1f..15f,
                            colors = SliderDefaults.colors(thumbColor = GoldPrimary, activeTrackColor = GoldPrimary)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                com.sentinelupi.frauddetector.ui.components.PhotoActionButton(
                    imageRes = com.sentinelupi.frauddetector.R.drawable.btn_pay_securely,
                    contentDescription = "Evaluate Threat Attribution",
                    modifier = Modifier.fillMaxWidth(),
                    height = 52.dp,
                    cornerRadius = 14.dp,
                    borderColor = GoldPrimary,
                    onClick = {
                        val amt = amountText.toDoubleOrNull() ?: 100.0
                        val cal = Calendar.getInstance().apply {
                            set(Calendar.HOUR_OF_DAY, hourIST)
                            set(Calendar.MINUTE, 15)
                        }
                        val txn = TransactionInput(
                            userId = profile.userId,
                            amount = amt,
                            category = selectedCategory,
                            deviceId = deviceIdText,
                            deviceModel = deviceModelText,
                            locationCity = selectedCity,
                            timestamp = cal.time,
                            burstVelocity1h = burstCount
                        )
                        val feats = FeatureExtractor.extract(profile, txn)
                        val (riskScore, tier) = FraudClassifier.predictRisk(feats)
                        latestResult = ExplainabilityEngine.generate(profile, txn, feats, riskScore, tier)
                    }
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Evaluation Result Display
        latestResult?.let { res ->
            val tierColor = when (res.riskTier) {
                "LOW" -> RiskLow
                "MEDIUM" -> RiskMedium
                "HIGH" -> RiskHigh
                else -> RiskCritical
            }

            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.5.dp, tierColor, RoundedCornerShape(16.dp)),
                colors = CardDefaults.cardColors(containerColor = DarkSurface),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = res.anomalyDiagnosis.replace("_", " "),
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold,
                            color = TextPrimary
                        )
                        Surface(
                            shape = RoundedCornerShape(12.dp),
                            color = tierColor.copy(alpha = 0.2f),
                            border = androidx.compose.foundation.BorderStroke(1.dp, tierColor)
                        ) {
                            Text(
                                text = "${res.riskScore} (${res.riskTier})",
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.ExtraBold,
                                color = tierColor
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(6.dp))
                    Text(text = res.summaryNarrative, fontSize = 12.sp, color = TextSecondary, lineHeight = 16.sp)
                    Spacer(modifier = Modifier.height(10.dp))
                    HorizontalDivider(color = DarkSurfaceBorder)
                    Spacer(modifier = Modifier.height(10.dp))

                    Text(text = "Factor Attribution Analysis:", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = TextPrimary)
                    Spacer(modifier = Modifier.height(6.dp))

                    res.factors.forEach { f ->
                        ThreatFactorItemRow(f)
                        Spacer(modifier = Modifier.height(4.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun PresetChip(label: String, onClick: () -> Unit) {
    Surface(
        shape = RoundedCornerShape(10.dp),
        color = DarkSurfaceElevated,
        border = androidx.compose.foundation.BorderStroke(1.dp, DarkSurfaceBorder),
        modifier = Modifier.clickable { onClick() }
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
            color = TextPrimary
        )
    }
}

@Composable
fun ThreatFactorItemRow(factor: RiskFactor) {
    val pillBg = when (factor.severity) {
        "CRITICAL" -> RiskCritical.copy(alpha = 0.2f)
        "ELEVATED" -> RiskMedium.copy(alpha = 0.2f)
        "TRUSTED" -> AccentIndigo.copy(alpha = 0.2f)
        else -> EmeraldGreen.copy(alpha = 0.2f)
    }
    val pillText = when (factor.severity) {
        "CRITICAL" -> RiskCritical
        "ELEVATED" -> RiskMedium
        "TRUSTED" -> AccentIndigo
        else -> EmeraldGreen
    }

    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.Top) {
        Surface(
            shape = RoundedCornerShape(4.dp),
            color = pillBg
        ) {
            Text(
                text = factor.severity,
                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = pillText
            )
        }
        Spacer(modifier = Modifier.width(8.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(text = factor.title, fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = TextPrimary)
            Text(text = factor.description, fontSize = 11.sp, color = TextSecondary, lineHeight = 15.sp)
        }
    }
}
