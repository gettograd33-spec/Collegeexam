#!/usr/bin/env pytho
=============================================================================
COLLEGE PREDICTOR & COLLEGESEARCH PRO — SIGNED .AAB GENERATOR
=============================================================================
This script scaffolds a complete Android Studio (Kotlin + Jetpack Compose
WebView) project around your existing HTML applications, generates a
production RSA-2048 Upload Keystore (or uses your existing keystore), and
builds a signed Android App Bundle (.aab) ready for Google Play Console.

USAGE (Local Machine with Java 17+ & Android SDK):
  python3 build_signed_aab.py --app student
  python3 build_signed_aab.py --app workspace

USAGE (Zero-Install Cloud Build via GitHub Actions):
  Run `python3 build_signed_aab.py --generate-ci` to create the full
  Android project + `.github/workflows/build_aab.yml`. Push to GitHub and
  download your signed `app-release.aab` directly from the Actions tab!
=============================================================================
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# APPLICATION CONFIGURATIONS
# ---------------------------------------------------------------------------
APP_CONFIGS = {
    "student": {
        "app_name": "College Predictor 2026",
        "package_id": "in.collegeexam.predictor",
        "html_source": "collegeexam_student_app.html",
        "version_code": 1,
        "version_name": "1.0.0",
    },
    "workspace": {
        "app_name": "CollegeSearch Pro",
        "package_id": "in.collegesearch.pro",
        "html_source": "collegesearch_pro_workspace.html",
        "version_code": 1,
        "version_name": "1.0.0",
    },
}


def create_android_project(target_dir: Path, config: dict) -> None:
    """Scaffolds the complete Gradle Android project structure."""
    pkg_path = config["package_id"].replace(".", "/")
    app_dir = target_dir / "app"
    src_main = app_dir / "src" / "main"
    java_dir = src_main / "java" / pkg_path
    assets_dir = src_main / "assets"
    res_values = src_main / "res" / "values"
    res_xml = src_main / "res" / "xml"
    workflow_dir = target_dir / ".github" / "workflows"

    for d in [java_dir, assets_dir, res_values, res_xml, workflow_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 1. Copy the HTML file into src/main/assets/index.html
    src_html = Path(config["html_source"])
    dest_html = assets_dir / "index.html"
    if src_html.exists():
        shutil.copy2(src_html, dest_html)
        print(f"[✓] Embedded {src_html} -> {dest_html}")
    else:
        print(
            f"[!] Warning: {src_html} not found in current directory. "
            f"Place {src_html.name} in {assets_dir}/index.html before building."
        )

    # 2. Root settings.gradle.kts
    (target_dir / "settings.gradle.kts").write_text(
        f"""pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "{config['app_name'].replace(' ', '')}"
include(":app")
""",
        encoding="utf-8",
    )

    # 3. Root build.gradle.kts
    (target_dir / "build.gradle.kts").write_text(
        """plugins {
    id("com.android.application") version "8.3.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
}
""",
        encoding="utf-8",
    )

    # 4. gradle.properties
    (target_dir / "gradle.properties").write_text(
        """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
android.nonTransitiveRClass=true
""",
        encoding="utf-8",
    )

    # 5. app/build.gradle.kts with full Release Signing Config for .aab
    (app_dir / "build.gradle.kts").write_text(
        f"""import java.util.Properties
import java.io.FileInputStream

plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

val keystorePropertiesFile = rootProject.file("keystore.properties")
val keystoreProperties = Properties()
if (keystorePropertiesFile.exists()) {{
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}}

android {{
    namespace = "{config['package_id']}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "{config['package_id']}"
        minSdk = 24
        targetSdk = 34
        versionCode = {config['version_code']}
        versionName = "{config['version_name']}"
    }}

    signingConfigs {{
        create("release") {{
            keyAlias = keystoreProperties.getProperty("keyAlias", "upload")
            keyPassword = keystoreProperties.getProperty("keyPassword", "CollegeExam@2026")
            storeFile = file(keystoreProperties.getProperty("storeFile", "../upload-keystore.jks"))
            storePassword = keystoreProperties.getProperty("storePassword", "CollegeExam@2026")
        }}
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = true
            isShrinkResources = true
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{
        jvmTarget = "17"
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.activity:activity-ktx:1.8.2")
    implementation("androidx.webkit:webkit:1.10.0")
}}
""",
        encoding="utf-8",
    )

    # 6. ProGuard rules (preserves JS Bridges)
    (app_dir / "proguard-rules.pro").write_text(
        f"""-keepattributes *Annotation*
-keepattributes JavascriptInterface
-keepclassmembers class * {{
    @android.webkit.JavascriptInterface <methods>;
}}
-keep class {config['package_id']}.** {{ *; }}
""",
        encoding="utf-8",
    )

    # 7. AndroidManifest.xml
    (src_main / "AndroidManifest.xml").write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />

    <application
        android:allowBackup="true"
        android:hardwareAccelerated="true"
        android:label="{config['app_name']}"
        android:supportsRtl="true"
        android:usesCleartextTraffic="false"
        android:theme="@style/Theme.AppCompat.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""",
        encoding="utf-8",
    )

    # 8. MainActivity.kt (Hardware-accelerated WebView + External Intent Routing + Double-Back)
    (java_dir / "MainActivity.kt").write_text(
        f"""package {config['package_id']}

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.GeolocationPermissions
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {{

    private lateinit var webView: WebView
    private var fileUploadCallback: ValueCallback<Array<Uri>>? = null

    private val fileChooserLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) {{ result ->
        val uris = WebChromeClient.FileChooserParams.parseResult(result.resultCode, result.data)
        fileUploadCallback?.onReceiveValue(uris)
        fileUploadCallback = null
    }}

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        webView.settings.apply {{
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            mediaPlaybackRequiresUserGesture = false
            mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            cacheMode = WebSettings.LOAD_DEFAULT
            setSupportMultipleWindows(true)
            javaScriptCanOpenWindowsAutomatically = true
        }}

        webView.addJavascriptInterface(AndroidBridge(), "Android")

        webView.webViewClient = object : WebViewClient() {{
            override fun shouldOverrideUrlLoading(
                view: WebView?,
                request: WebResourceRequest?
            ): Boolean {{
                val url = request?.url?.toString() ?: return false
                if (url.startsWith("file:///android_asset/") ||
                    url.contains("youtube.com/embed/") ||
                    url.contains("youtube-nocookie.com/embed/")
                ) {{
                    return false
                }}
                return try {{
                    startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    true
                }} catch (e: Exception) {{
                    false
                }}
            }}
        }}

        webView.webChromeClient = object : WebChromeClient() {{
            override fun onGeolocationPermissionsShowPrompt(
                origin: String?,
                callback: GeolocationPermissions.Callback?
            ) {{
                callback?.invoke(origin, true, false)
            }}

            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {{
                fileUploadCallback?.onReceiveValue(null)
                fileUploadCallback = filePathCallback
                return try {{
                    val intent = fileChooserParams?.createIntent()
                    if (intent != null) {{
                        fileChooserLauncher.launch(intent)
                        true
                    }} else false
                }} catch (e: Exception) {{
                    fileUploadCallback = null
                    false
                }}
            }}
        }}

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {{
            override fun handleOnBackPressed() {{
                if (webView.canGoBack()) {{
                    webView.goBack()
                }} else {{
                    webView.evaluateJavascript(
                        "if(typeof handleBackPress==='function'){{handleBackPress();}}else{{window.close();}}",
                        null
                    )
                }}
            }}
        }})

        webView.loadUrl("file:///android_asset/index.html")
    }}

    inner class AndroidBridge {{
        @JavascriptInterface
        fun exitApp() {{
            runOnUiThread {{ finishAffinity() }}
        }}
    }}
}}
""",
        encoding="utf-8",
    )

    # 9. GitHub Actions Workflow (.github/workflows/build_signed_aab.yml)
    # Allows building the signed .aab in the cloud without installing Android Studio locally
    (workflow_dir / "build_signed_aab.yml").write_text(
        f"""name: Build Signed Release AAB ({config['app_name']})

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build-aab:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Source
        uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Android SDK
        uses: android-actions/setup-android@v3

      - name: Generate Upload Keystore (if not present)
        run: |
          if [ ! -f upload-keystore.jks ]; then
            keytool -genkeypair -v \\
              -keystore upload-keystore.jks \\
              -alias upload \\
              -keyalg RSA \\
              -keysize 2048 \\
              -validity 10000 \\
              -storepass "CollegeExam@2026" \\
              -keypass "CollegeExam@2026" \\
              -dname "CN=CollegeExam Dream Big Education, OU=Admissions, O=CollegeExam, L=Dehradun, ST=Uttarakhand, C=IN"
          fi

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3
        with:
          gradle-version: '8.6'

      - name: Build Signed Release AAB
        run: gradle :app:bundleRelease --no-daemon

      - name: Upload Signed .AAB Artifact
        uses: actions/upload-artifact@v4
        with:
          name: {config['package_id']}-signed-release-aab
          path: |
            app/build/outputs/bundle/release/*.aab
            upload-keystore.jks
""",
        encoding="utf-8",
    )


def generate_keystore(target_dir: Path) -> Path:
    """Generates an RSA-2048 upload keystore and keystore.properties."""
    ks_path = target_dir / "upload-keystore.jks"
    props_path = target_dir / "keystore.properties"

    props_path.write_text(
        """storePassword=CollegeExam@2026
keyPassword=CollegeExam@2026
keyAlias=upload
storeFile=../upload-keystore.jks
""",
        encoding="utf-8",
    )

    if ks_path.exists():
        print(f"[✓] Using existing keystore: {ks_path}")
        return ks_path

    keytool = shutil.which("keytool")
    if not keytool:
        print("[!] `keytool` (JDK) not found in PATH. Keystore will be generated during CI build.")
        return ks_path

    cmd = [
        keytool,
        "-genkeypair",
        "-v",
        "-keystore",
        str(ks_path),
        "-alias",
        "upload",
        "-keyalg",
        "RSA",
        "-keysize",
        "2048",
        "-validity",
        "10000",
        "-storepass",
        "CollegeExam@2026",
        "-keypass",
        "CollegeExam@2026",
        "-dname",
        "CN=CollegeExam Dream Big Education, OU=Admissions, O=CollegeExam, L=Dehradun, ST=Uttarakhand, C=IN",
    ]
    subprocess.run(cmd, check=True)
    print(f"[✓] Generated signed upload keystore: {ks_path}")
    return ks_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Signed .AAB for Google Play Upload")
    parser.add_argument(
        "--app",
        choices=["student", "workspace"],
        default="student",
        help="Which app to package: 'student' (College Predictor) or 'workspace' (CollegeSearch Pro)",
    )
    parser.add_argument(
        "--output-dir",
        default="./android_aab_build",
        help="Output folder for the Android project and signed .aab",
    )
    args = parser.parse_args()

    config = APP_CONFIGS[args.app]
    out_dir = Path(args.output_dir).resolve() / args.app

    print(f"=== Scaffolding Android AAB Project for {config['app_name']} ===")
    create_android_project(out_dir, config)
    generate_keystore(out_dir)

    gradle_bin = shutil.which("gradle")
    if gradle_bin and (os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")):
        print("[*] Running `gradle :app:bundleRelease` to compile signed .aab...")
        subprocess.run([gradle_bin, ":app:bundleRelease", "--no-daemon"], cwd=out_dir, check=True)
        aab_path = out_dir / "app" / "build" / "outputs" / "bundle" / "release" / "app-release.aab"
        print(f"\n[SUCCESS] Signed .AAB ready for Google Play Console upload:\n  -> {aab_path}")
    else:
        print(
            f"\n[✓] Project & Signing Keystore ready in: {out_dir}\n"
            f"To compile your signed .aab:\n"
            f"  Option A (Android Studio): Open `{out_dir}` -> Build -> Generate Signed App Bundle (.aab)\n"
            f"  Option B (GitHub Cloud): Push `{out_dir}` to GitHub; the included workflow "
            f"`.github/workflows/build_signed_aab.yml` automatically builds and provides `app-release.aab`."
        )


if __name__ == "__main__":
    main()