# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Clinic Scheduling Agent Tools."""

from datetime import datetime, time

# --- Mock Data ---
DOCTORS = {
    "Cardiology": ["Dr. Alice Martin", "Dr. Bob Chen"],
    "Neurology": ["Dr. Carol White", "Dr. David Green"],
    "Orthopedics": ["Dr. Eve Black", "Dr. Frank Blue"],
}

APPOINTMENT_HISTORY = [
    {
        "id": "appt_1",
        "department": "Cardiology",
        "doctor": "Dr. Alice Martin",
        "date": "2023-10-26",
    },
    {
        "id": "appt_2",
        "department": "Orthopedics",
        "doctor": "Dr. Eve Black",
        "date": "2023-08-15",
    },
]


def get_doctors_for_department(department: str) -> dict:
    """
    Passthrough tool to transition the UI to the doctor selection screen.

    In a real application, this tool would fetch doctors for the given
    department from a database. Here, it just confirms the transition.

    Args:
        department: The medical department selected by the user.

    Returns:
        A dictionary containing the department and a list of doctor names.
    """
    # # print(f"\n--- 🛠️ TOOL CALL: get_doctors_for_department (department='{department}') ---")
    doctors = DOCTORS.get(department, [])
    # The A2UI ChoicePicker requires options in {label, value} format.
    # While the template is static, a real tool would return this structure.
    doctor_options = [{"label": name, "value": name} for name in doctors]
    result = {
        "status": "success",
        "department": department,
        "doctors": doctor_options,
    }
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result


def check_doctor_availability(
    doctor: str | list[str],
    patient_name: str,
    patient_age: str,
    patient_weight: str,
    first_visit: bool = False,
) -> dict:
    """
    Passthrough tool to process the patient intake form and transition
    to the scheduling screen.

    Args:
        doctor: The doctor selected from the ChoicePicker. This will be a list.
        patient_name: The patient's full name.
        patient_age: The patient's age.
        patient_weight: The patient's weight.
        first_visit: Whether this is the patient's first visit.

    Returns:
        A dictionary containing the processed form data.
    """
    # # print(f"\n--- 🛠️ TOOL CALL: check_doctor_availability (...) ---")
    # ChoicePicker values are returned as a list, even for single-select.
    if isinstance(doctor, list):
        doctor = doctor[0] if doctor else ""

    result = {
        "status": "success",
        "doctor": doctor,
        "patient_name": patient_name,
        "patient_age": patient_age,
        "patient_weight": patient_weight,
        "first_visit": first_visit,
    }
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result


def confirm_appointment(
    doctor: str | list[str],
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
) -> dict:
    """
    Finalizes the appointment booking.

    Args:
        doctor: The selected doctor. ChoicePicker may supply this as a list.
        patient_name: The patient's name.
        appointment_date: The preferred date from DateTimeInput (ISO datetime).
        appointment_time: The preferred time from DateTimeInput. The time picker
            has enableDate=false, so this is normally time-only (e.g. "14:30").

    Returns:
        A dictionary with all confirmed appointment details for display.
    """
    # # print(f"\n--- 🛠️ TOOL CALL: confirm_appointment (...) ---")
    # ChoicePicker.value is a DynamicStringList, so the doctor may arrive as
    # a single-element list rather than a bare string.
    if isinstance(doctor, list):
        doctor = doctor[0] if doctor else ""

    # DateTimeInput sends an ISO string. The date picker (enableTime=false)
    # sends a full datetime; the time picker (enableDate=false) sends a
    # time-only value, which datetime.fromisoformat cannot parse.
    try:
        if not appointment_date or not appointment_time:
            raise ValueError("Missing date or time")
        # Extract YYYY-MM-DD
        formatted_date = datetime.fromisoformat(appointment_date.replace("Z", "+00:00")).strftime("%B %d, %Y")
        
        # Extract HH:MM AM/PM, accepting either "14:30" or a full datetime.
        raw_time = (appointment_time or "").replace("Z", "+00:00")
        try:
            parsed_time = time.fromisoformat(raw_time)
        except ValueError:
            parsed_time = datetime.fromisoformat(raw_time)
        formatted_time = parsed_time.strftime("%I:%M %p")
    except (ValueError, TypeError, AttributeError):
        result = {"error": "Please select a date and time in the UI before confirming."}
    # # print(f"Returns: {result}\n--------------------------------------\n")
        return result

    result = {
        "status": "confirmed",
        "doctor": doctor,
        "patient_name": patient_name,
        "appointment_date": formatted_date,
        "appointment_time": formatted_time,
    }
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result


def get_appointment_history() -> dict:
    """
    Retrieves the user's past appointments.

    Returns:
        A dictionary containing a list of appointment records.
    """
    # print("\n--- 🛠️ TOOL CALL: get_appointment_history ---")
    result = {"appointments": APPOINTMENT_HISTORY}
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result


def reset_to_departments() -> dict:
    """
    Passthrough tool to signal a UI reset to the department selection screen.
    """
    # print("\n--- 🛠️ TOOL CALL: reset_to_departments ---")
    result = {"status": "reset_to_departments"}
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result


def restart_flow() -> dict:
    """
    Passthrough tool to signal a UI reset to the main welcome screen.
    """
    # print("\n--- 🛠️ TOOL CALL: restart_flow ---")
    result = {"status": "restarted"}
    # # print(f"Returns: {result}\n--------------------------------------\n")
    return result