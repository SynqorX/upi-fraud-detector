package com.sentinelupi.frauddetector.model

import com.sentinelupi.frauddetector.engine.EvaluationResult

data class UpiTransactionRecord(
    val id: String,
    val title: String,
    val peerUpi: String,
    val amount: Double,
    val isDebit: Boolean,
    val status: String, // "SUCCESS", "BLOCKED", "RECEIVED"
    val timestamp: Long = System.currentTimeMillis(),
    val riskScore: Double = 0.0,
    val riskTier: String = "LOW",
    val note: String = "UPI Transfer",
    val explanation: EvaluationResult? = null
)
