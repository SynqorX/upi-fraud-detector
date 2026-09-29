package com.sentinelupi.frauddetector.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightMinimalistGlassColorScheme = lightColorScheme(
    primary = MintPrimary,
    onPrimary = Color.White,
    primaryContainer = MintLight,
    onPrimaryContainer = InkDark,
    secondary = SkyPrimary,
    onSecondary = Color.White,
    secondaryContainer = SkyLight,
    onSecondaryContainer = InkDark,
    tertiary = SkyPrimary,
    onTertiary = Color.White,
    background = PageBg,
    surface = Color.White,
    surfaceVariant = GlassElevated,
    onBackground = InkDark,
    onSurface = InkDark,
    onSurfaceVariant = InkMuted,
    outline = GlassBorderSubtle
)

@Composable
fun SentinelTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightMinimalistGlassColorScheme,
        typography = SentinelTypography,
        content = content
    )
}
