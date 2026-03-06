package com.example.skoolplannr_flutter

import android.content.Context
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.embedding.android.FlutterActivity
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
	override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
		super.configureFlutterEngine(flutterEngine)

		MethodChannel(
			flutterEngine.dartExecutor.binaryMessenger,
			"schoolplannr/upcoming_widget"
		).setMethodCallHandler { call, result ->
			if (call.method != "updateUpcomingClasses") {
				result.notImplemented()
				return@setMethodCallHandler
			}

			val classesJson = call.argument<String>("classes") ?: "[]"
			val prefs = getSharedPreferences(
				UpcomingClassesWidgetProvider.PREFS_NAME,
				Context.MODE_PRIVATE
			)

			prefs.edit()
				.putString(UpcomingClassesWidgetProvider.KEY_CLASSES_JSON, classesJson)
				.apply()

			UpcomingClassesWidgetProvider.updateAllWidgets(applicationContext)
			result.success(null)
		}
	}
}
