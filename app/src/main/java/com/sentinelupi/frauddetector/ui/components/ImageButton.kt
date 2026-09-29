package com.sentinelupi.frauddetector.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.ripple.rememberRipple
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.sentinelupi.frauddetector.ui.theme.DarkSurfaceBorder
import com.sentinelupi.frauddetector.ui.theme.GoldPrimary
import com.sentinelupi.frauddetector.ui.theme.OrangePrimary

/**
 * Reusable Photo Image Button that renders customized graphical buttons from the photo folder
 * with smooth press feedback, rounded corners, and a subtle glowing gold/orange border.
 */
@Composable
fun PhotoActionButton(
    @DrawableRes imageRes: Int,
    contentDescription: String?,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    height: Dp = 54.dp,
    cornerRadius: Dp = 14.dp,
    borderColor: Color = GoldPrimary.copy(alpha = 0.5f),
    onClick: () -> Unit
) {
    Box(
        modifier = modifier
            .height(height)
            .shadow(6.dp, RoundedCornerShape(cornerRadius), ambientColor = OrangePrimary, spotColor = GoldPrimary)
            .clip(RoundedCornerShape(cornerRadius))
            .border(1.5.dp, if (enabled) borderColor else DarkSurfaceBorder, RoundedCornerShape(cornerRadius))
            .clickable(
                enabled = enabled,
                interactionSource = remember { MutableInteractionSource() },
                indication = rememberRipple(bounded = true, color = GoldPrimary),
                onClick = onClick
            ),
        contentAlignment = Alignment.Center
    ) {
        Image(
            painter = painterResource(id = imageRes),
            contentDescription = contentDescription,
            contentScale = ContentScale.Crop,
            modifier = Modifier.fillMaxSize(),
            alpha = if (enabled) 1.0f else 0.45f
        )
    }
}
