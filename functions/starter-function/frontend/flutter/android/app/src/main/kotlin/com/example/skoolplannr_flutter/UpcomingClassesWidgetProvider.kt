package com.example.skoolplannr_flutter

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import com.notacoder.schoolplannr.R
import org.json.JSONArray

class UpcomingClassesWidgetProvider : AppWidgetProvider() {
    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        appWidgetIds.forEach { appWidgetId ->
            updateWidget(context, appWidgetManager, appWidgetId)
        }
    }

    companion object {
        const val PREFS_NAME = "upcoming_classes_widget"
        const val KEY_CLASSES_JSON = "upcoming_classes_json"

        fun updateAllWidgets(context: Context) {
            val manager = AppWidgetManager.getInstance(context)
            val provider = ComponentName(context, UpcomingClassesWidgetProvider::class.java)
            val widgetIds = manager.getAppWidgetIds(provider)

            widgetIds.forEach { widgetId ->
                updateWidget(context, manager, widgetId)
            }
        }

        private fun updateWidget(
            context: Context,
            manager: AppWidgetManager,
            appWidgetId: Int
        ) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            val classesJson = prefs.getString(KEY_CLASSES_JSON, "[]") ?: "[]"
            val lines = buildLines(classesJson)

            val views = RemoteViews(context.packageName, R.layout.widget_upcoming_classes)
            views.setTextViewText(R.id.widget_classes_text, lines)

            val launchIntent = Intent(context, MainActivity::class.java)
            val pendingIntent = PendingIntent.getActivity(
                context,
                0,
                launchIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_root, pendingIntent)

            manager.updateAppWidget(appWidgetId, views)
        }

        private fun buildLines(classesJson: String): String {
            return try {
                val entries = JSONArray(classesJson)
                if (entries.length() == 0) {
                    return "No upcoming classes"
                }

                val lines = mutableListOf<String>()
                val count = minOf(entries.length(), 4)
                for (index in 0 until count) {
                    val item = entries.getJSONObject(index)
                    val subject = item.optString("subject", "Class")
                    val day = item.optString("day", "")
                    val startTime = item.optString("startTime", "")
                    val endTime = item.optString("endTime", "")
                    val detail = listOf(day, "$startTime-$endTime")
                        .joinToString(" ")
                        .trim()

                    lines.add("$detail  $subject")
                }

                lines.joinToString("\n")
            } catch (_: Exception) {
                "No upcoming classes"
            }
        }
    }
}
