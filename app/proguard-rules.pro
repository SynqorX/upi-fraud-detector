# Proguard rules for SentinelUPI
-keepattributes *Annotation*
-keepclassmembers class * {
    @androidx.annotation.Keep *;
}
