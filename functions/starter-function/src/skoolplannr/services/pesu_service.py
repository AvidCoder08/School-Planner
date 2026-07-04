from typing import Any, Dict, Optional

try:
    from pesuacademy import PESUAcademy
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        "Missing dependency 'pesuacademy'. Run run.bat or install requirements.txt."
    ) from exc


class PesuServiceError(Exception):
    pass


class PesuService:
    async def get_attendance(
        self,
        *,
        username: str,
        password: str,
        semester: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not username.strip() or not password:
            raise PesuServiceError("PESU username and password are required.")

        client = None
        try:
            client = await PESUAcademy.login(username=username.strip(), password=password)
            attendance_by_semester = await client.get_attendance(semester=semester)

            total_attended = 0
            total_classes = 0
            semesters: list[Dict[str, Any]] = []

            for sem in sorted(attendance_by_semester.keys()):
                courses = attendance_by_semester.get(sem, [])
                normalized_courses: list[Dict[str, Any]] = []

                for course in courses:
                    attendance = course.attendance
                    attended = attendance.attended if attendance else None
                    total = attendance.total if attendance else None
                    percentage = attendance.percentage if attendance else None

                    if isinstance(attended, int) and isinstance(total, int) and total > 0:
                        total_attended += attended
                        total_classes += total

                    normalized_courses.append(
                        {
                            "code": course.code,
                            "title": course.title,
                            "attended": attended,
                            "total": total,
                            "percentage": percentage,
                        }
                    )

                semesters.append(
                    {
                        "semester": sem,
                        "courses": normalized_courses,
                    }
                )

            overall_percentage = None
            if total_classes > 0:
                overall_percentage = round((total_attended / total_classes) * 100, 2)

            return {
                "semesters": semesters,
                "overall_percentage": overall_percentage,
                "total_attended": total_attended,
                "total_classes": total_classes,
            }
        except Exception as exc:
            raise PesuServiceError(f"Failed to fetch attendance from PESU Academy: {exc}") from exc
        finally:
            if client is not None:
                await client.close()
