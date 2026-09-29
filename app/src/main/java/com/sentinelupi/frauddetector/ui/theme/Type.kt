package com.sentinelupi.frauddetector.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Modern Clean Sans-Serif Typography matching preview.html (Plus Jakarta Sans & Space Grotesk)
val ModernSans = FontFamily.Default
val ClassicSerif = FontFamily.Default

val SentinelTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 52.sp,
        lineHeight = 60.sp,
        letterSpacing = (-0.5).sp,
        color = InkDark
    ),
    displayMedium = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Bold,
        fontSize = 40.sp,
        lineHeight = 48.sp,
        letterSpacing = (-0.25).sp,
        color = InkDark
    ),
    displaySmall = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Bold,
        fontSize = 32.sp,
        lineHeight = 40.sp,
        letterSpacing = 0.sp,
        color = InkDark
    ),
    headlineLarge = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
        lineHeight = 36.sp,
        letterSpacing = (-0.25).sp,
        color = InkDark
    ),
    headlineMedium = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.SemiBold,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp,
        color = InkDark
    ),
    headlineSmall = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.SemiBold,
        fontSize = 20.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp,
        color = InkDark
    ),
    titleLarge = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.SemiBold,
        fontSize = 18.sp,
        lineHeight = 26.sp,
        letterSpacing = 0.sp,
        color = InkDark
    ),
    titleMedium = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Medium,
        fontSize = 15.sp,
        lineHeight = 22.sp,
        letterSpacing = 0.1.sp,
        color = InkDark
    ),
    titleSmall = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Medium,
        fontSize = 13.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.1.sp,
        color = InkDark
    ),
    bodyLarge = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Normal,
        fontSize = 15.sp,
        lineHeight = 22.sp,
        letterSpacing = 0.15.sp,
        color = InkDark
    ),
    bodyMedium = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.1.sp,
        color = InkMuted
    ),
    bodySmall = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Normal,
        fontSize = 11.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.2.sp,
        color = InkSubtle
    ),
    labelLarge = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.SemiBold,
        fontSize = 13.sp,
        lineHeight = 18.sp,
        letterSpacing = 0.1.sp,
        color = InkDark
    ),
    labelMedium = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.3.sp,
        color = InkMuted
    ),
    labelSmall = TextStyle(
        fontFamily = ModernSans,
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.4.sp,
        color = InkSubtle
    )
)
