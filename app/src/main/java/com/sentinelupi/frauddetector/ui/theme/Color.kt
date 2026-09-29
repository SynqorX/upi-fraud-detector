package com.sentinelupi.frauddetector.ui.theme

import androidx.compose.ui.graphics.Color

// Light Minimalist Glassmorphism Palette (Matches preview.html)
val PageBg = Color(0xFFF8FAFC)                // Clean Airy Slate Page Background
val GlassLight = Color(0xB8FFFFFF)             // 72% Translucent Frosted Glass
val GlassElevated = Color(0xD9FFFFFF)          // 85% Translucent Floating Glass
val GlassBorder = Color(0xF2FFFFFF)            // 95% Pure White Border
val GlassBorderSubtle = Color(0xB3E2E8F0)      // Subtle 70% Slate-200 Border

// Brand Accent Colors
val MintPrimary = Color(0xFF10B981)            // Emerald / Mint Green Primary
val MintLight = Color(0xFFD1FAE5)              // Soft Mint Pill Fill
val MintGlow = Color(0x2610B981)               // 15% Mint Glow

val SkyPrimary = Color(0xFF0284C7)             // Sky Blue Primary
val SkyLight = Color(0xFFE0F2FE)               // Soft Sky Pill Fill
val SkyGlow = Color(0x260284C7)                // 15% Sky Glow

// Typography & Ink (Slate Ink Scale)
val InkDark = Color(0xFF0F172A)                // Slate 900 Deep Text
val InkMuted = Color(0xFF64748B)               // Slate 500 Subtitle Text
val InkSubtle = Color(0xFF94A3B8)              // Slate 400 Micro Text
val InkBorder = Color(0xFFE2E8F0)              // Slate 200 Card Border

// Risk / Security Interception Colors
val RiskLow = Color(0xFF10B981)                // Verified / Safe Mint
val RiskMedium = Color(0xFFF59E0B)             // Amber Caution
val RiskHigh = Color(0xFFF97316)               // Orange Elevated Alert
val RiskCritical = Color(0xFFEF4444)           // Critical Block Red
val RiskCriticalLight = Color(0xFFFEE2E2)      // Red 100 Pill Fill
val RiskCriticalBorder = Color(0x66FCA5A5)     // Red 300 Subtle Border

// Card Hero Gradient Colors
val CardHeroGradStart = Color(0xF2FFFFFF)      // 95% White
val CardHeroGradMid = Color(0xE6F0FDFA)        // Mint-tinted Glass
val CardHeroGradEnd = Color(0xE6F0F9FF)        // Sky-tinted Glass

// Backward Compatibility Aliases
val DarkBackground = PageBg
val DarkSurface = GlassLight
val DarkSurfaceElevated = GlassElevated
val DarkSurfaceBorder = GlassBorderSubtle
val DarkSurfaceVariant = GlassElevated
val TextPrimary = InkDark
val TextSecondary = InkMuted
val TextMuted = InkSubtle
val GoldPrimary = MintPrimary
val GoldLight = MintLight
val GoldDark = SkyPrimary
val GoldGlow = MintGlow
val OrangePrimary = SkyPrimary
val OrangeLight = SkyLight
val OrangeDark = SkyPrimary
val OrangeGlow = SkyGlow
val CardGradientStart = CardHeroGradStart
val CardGradientEnd = CardHeroGradEnd
val AttackGradientStart = RiskCriticalLight
val AttackGradientEnd = Color.White
val EmeraldGreen = MintPrimary
val AccentIndigo = SkyPrimary
val AccentCyan = SkyLight
val AccentPurple = SkyPrimary
val AccentAmber = RiskMedium
val AccentHoney = RiskMedium
val AccentGold = MintPrimary
val AccentOrange = SkyPrimary
