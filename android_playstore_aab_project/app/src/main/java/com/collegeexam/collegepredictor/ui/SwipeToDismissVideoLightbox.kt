package com.collegeexam.collegepredictor.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import kotlin.math.abs

@Composable
fun SwipeToDismissVideoLightbox(
    onDismiss: () -> Unit,
    content: @Composable () -> Unit
) {
    val coroutineScope = rememberCoroutineScope()
    val offsetY = remember { Animatable(0f) }
    val dismissThreshold = 400f

    val dragProgress = (abs(offsetY.value) / dismissThreshold).coerceIn(0f, 1f)
    val backgroundAlpha = 1f - dragProgress

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0x990A0A0A).copy(alpha = backgroundAlpha * 0.85f))
            .clickable(
                interactionSource = remember { MutableInteractionSource() },
                indication = null,
                onClick = onDismiss
            ),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth(0.95f)
                .aspectRatio(16f / 9f)
                .graphicsLayer {
                    translationY = offsetY.value
                    val scale = 1f - (dragProgress * 0.1f)
                    scaleX = scale
                    scaleY = scale
                    alpha = 1f - (dragProgress * 0.5f)
                }
                .pointerInput(Unit) {
                    detectVerticalDragGestures(
                        onDragEnd = {
                            coroutineScope.launch {
                                if (abs(offsetY.value) > dismissThreshold) {
                                    val targetValue = if (offsetY.value > 0) 1500f else -1500f
                                    offsetY.animateTo(targetValue, animationSpec = tween(300))
                                    onDismiss()
                                } else {
                                    offsetY.animateTo(0f, animationSpec = tween(300))
                                }
                            }
                        },
                        onDragCancel = {
                            coroutineScope.launch {
                                offsetY.animateTo(0f, animationSpec = tween(300))
                            }
                        },
                        onVerticalDrag = { change, dragAmount ->
                            change.consume()
                            coroutineScope.launch {
                                offsetY.snapTo(offsetY.value + dragAmount)
                            }
                        }
                    )
                }
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null,
                    onClick = {}
                )
                .clip(RoundedCornerShape(16.dp))
                .background(Color.Black)
        ) {
            content()
        }
    }
}
