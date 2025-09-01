from django.urls import path, include
from .timetable_views import staff_timetable
from .student_timetable_views import student_timetable
from .views import *

from .profile_views import staff_profile, hod_profile
from .view_mentees import view_mentees



urlpatterns = [
    path('staff/my_class/', my_class_students, name='staff_my_class'),
    path("",dash,name='dash'),
    path("notifications/", notifications_view, name="notifications_view"),
    path("profile/", student_profile, name='student_profile'),
    path("staff/profile/", staff_profile, name='staff_profile'),
    path("hod/profile/", hod_profile, name='hod_profile'),
    path("od/",od,name='od'),
    path("od/upload_proof_od/<int:id>",upload_proof_od,name='proof_od'),
    path("leave/",leave,name='leave'),
    path("leave/upload_proof_od/<int:id>",upload_proof_leave,name='proof_leave'),
    path("gatepass/",gatepass,name='gatepass'),
    path("feedback",student_feedback,name='student_feedback'),
    path("feedbackform/<int:id>/<str:typ>",student_feedback_form,name='student_feedback_form'),
    path('bonafide/', bonafide_view, name='bonafide'),
    path("dash/", ahod_dash, name="ahod_dash"),
    path('student/timetable/', student_timetable, name='student_timetable'),
    path("ahod/", include("core.ahod_urls")),


    # Staff list for HOD
    path('hod/staff-list/', staff_list, name='staff_list'),
    path('hod/staff/<int:staff_id>/mentees/', view_mentees, name='view_mentees'),


]

from .ahod_actions import ahod_action_od
from .ahod_actions_leave import ahod_action_leave

urlpatterns += [
    path("ahods/check", ahod_od_view, name='ahod_od_view'),
    path("ahleaves/check", ahod_leave_view, name='ahod_leave_view'),
    path("ahods/action/<int:id>", ahod_action_od, name="ahod_action_od"),
    path("ahleaves/action/<int:id>", ahod_action_leave, name="ahod_action_leave"),

]
# staff

urlpatterns += [
    path("ods/check",staff_od_view,name='staff_od_view'),
    path("ods/action/<int:id>",staff_action_od,name='staff_action_od'),
    path("leaves/check",staff_leave_view,name='staff_leave_view'),
    path("leaves/action/<int:id>",staff_action_leave,name='staff_action_leave'),
    path("gatepasss/check",staff_gatepass_view,name='staff_gatepass_view'),
    path("gatepass/action/<int:id>",staff_action_gatepass,name='staff_action_gatepass'),
    path("bonafide/action/<int:id>", staff_action_bonafide, name="staff_action_bonafide"),
    path("bonafides/", staff_bonafides, name="staff_bonafides"),
    path("staff/notifications/", staff_notifications_view, name="staff_notifications"),
    path("timetable/", staff_timetable, name="staff_timetable"),
    path("my_class_students/", my_class_students, name="my_class_students"),

]
# hod

urlpatterns += [
    path("hods/check",hod_od_view,name='hod_od_view'),
    path("hleaves/check",hod_leave_view,name='hod_leave_view'),
    path("hgatepass/check",hod_gatepass_view,name='hod_gatepass_view'),
    path("hfeed/",hod_feedback_view,name="hod_feedback_view"),
    path("hfeed/toogle/<int:id>",hod_feedback_toggle,name='hod_feedback_toggle'),
    path("hfeed/hod_spot_feedback",hod_spot_feedback,name='hod_spot_feedback'),
    path("hfeed/spottoogle/<int:id>",hod_spot_feedback_toggle,name='hod_spot_feedback_toggle'),
    path("hbonafide/", hod_bonafide_view, name="hod_bonafide_view"),
    
        path('hod/notifications/', hod_notification_history, name='hod_notification_history'),
]


# AHOD
urlpatterns += [
    path("bonafide-hod/", ahod_bonafide_hod, name="ahod_bonafide_hod"),
    path("gatepass-hod/", ahod_gatepass_hod, name="ahod_gatepass_hod"),
]

urlpatterns += [
    path("ahod/notifications/", ahod_notification_history, name="ahod_notification_history"),
]

# auth
urlpatterns+=[
    path("login",login_user,name='login'),
    path("logout",logout_user,name='logout')
]



# API

# R & D

# Placement




