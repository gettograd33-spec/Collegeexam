package com.collegeexam.collegepredictor.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer

class VideoPlayerViewModel : ViewModel() {
    private var exoPlayer: ExoPlayer? = null

    fun getOrCreatePlayer(context: Context, streamUrl: String): ExoPlayer {
        val player = exoPlayer ?: ExoPlayer.Builder(context.applicationContext).build().also {
            exoPlayer = it
        }
        val mediaItem = MediaItem.fromUri(streamUrl)
        if (player.currentMediaItem != mediaItem) {
            player.setMediaItem(mediaItem)
            player.prepare()
            player.playWhenReady = true
        }
        return player
    }

    fun stopAndReleasePlayer() {
        exoPlayer?.stop()
        exoPlayer?.release()
        exoPlayer = null
    }

    override fun onCleared() {
        super.onCleared()
        stopAndReleasePlayer()
    }
}
