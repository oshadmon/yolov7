#---------------------------------------------------------------------------------------------------------------------#
# Policy for live data coming from publish_data.py script  - the policy uses cv2
# :sample policy:
# {
#    'dbms': 'livefeed',
#    'table': '2024_05_30_13_33_15_566021_mp4',
#    'file_name': '2024_05_30_13_33_15_566021.mp4',
#    'readings': {
#        'start_time': '2024-05-30 13:33:05.514531',
#        'end_time': '2024-05-30 13:33:15.559898',
#        'duration': 10.05
#    },
#    'frame_count': 278,
#    'fps': 20.0,
#    'duration': 13.9,
#    'frames': [
#        ...
#        [138, 168, 120],
#        [148, 178, 130],
#        [152, 182, 134]]], dtype=uint8)
#    ]
# }
#---------------------------------------------------------------------------------------------------------------------#

set new_policy = ""
policy_id = livefeed
is_policy = blockchain get mapping where id = !policy_id
if !is_policy then goto msg-call

:create-policy;
set new_policy = ""
set policy new_policy [mapping] = {}
set policy new_policy [mapping][id] = !policy_id
set policy new_policy [mapping][dbms] = "bring [dbms]"
set policy new_policy [mapping][table] = "bring [table]"
set policy new_policy [mapping][readings] = "readings"

# -- readings --
set policy new_policy [mapping][schema] = {}
set policy new_policy [mapping][schema][start_time] = {}
set policy new_policy [mapping][schema][start_time][type] = "timestamp"
set policy new_policy [mapping][schema][start_time][default] = "now()"
set policy new_policy [mapping][schema][start_time][bring] = "[start_time]"

set policy new_policy [mapping][schema][end_time] = {}
set policy new_policy [mapping][schema][end_time][type] = "timestamp"
set policy new_policy [mapping][schema][end_time][default] = "now()"
set policy new_policy [mapping][schema][end_time][bring] = "[end_time]"

set policy new_policy [mapping][schema][duration] = {}
set policy new_policy [mapping][schema][duration][type] = "float"
# set policy new_policy [mapping][schema][duration][default] = 0.0
set policy new_policy [mapping][schema][duration][bring] = "[start_time]"

# -- video insight --
set policy new_policy [mapping][schema][frame_count] = {}
set policy new_policy [mapping][schema][frame_count][type] = "int"
set policy new_policy [mapping][schema][frame_count][bring] = "[frame_count]"
# set policy new_policy [mapping][schema][frame_count][default] = 0
set policy new_policy [mapping][schema][frame_count][root] = true.bool

set policy new_policy [mapping][schema][fps] = {}
set policy new_policy [mapping][schema][fps][type] = "float"
set policy new_policy [mapping][schema][fps][bring] = "[fps]"
# set policy new_policy [mapping][schema][fps][default] = 0.0
set policy new_policy [mapping][schema][fps][root] = true.bool

set policy new_policy [mapping][schema][file] = {}
set policy new_policy [mapping][schema][file][blob] = true.bool
set policy new_policy [mapping][schema][file][bring] = "[video_base64]"
set policy new_policy [mapping][schema][file][extension] = "mp4"
set policy new_policy [mapping][schema][file][hash] = "md5"
set policy new_policy [mapping][schema][file][type] = "varchar"
set policy new_policy [mapping][schema][file][apply] = "base64decoding"
# set policy new_policy [mapping][schema][file][apply] = "opencv"
set policy new_policy [mapping][schema][file][root] = true.bool
set policy new_policy [mapping][schema][file][default] = ""



:test-policy:
test_policy = json !new_policy test
if !test_policy == false then goto test-policy-error

:publish-policy:
process !local_scripts/policies/publish_policy.al
if !error_code == 1 then goto sign-policy-error
if !error_code == 2 then goto prepare-policy-error
if !error_code == 3 then goto declare-policy-error


:msg-call:
if !is_demo == true then goto end-script
on error goto msg-error
if !anylog_broker_port then
<do run msg client where broker=local and port=!anylog_broker_port and log=false and topic=(
    name=!policy_id and
    policy=!policy_id
)>
else if not !anylog_broker_port and !user_name and !user_password then
<do run msg client where broker=rest and port=!anylog_rest_port and user=!user_name and password=!user_password and user-agent=anylog and log=false and topic=(
    name=!policy_id and
    policy=!policy_id
)>
else if not !anylog_broker_port then
<do run msg client where broker=rest and port=!anylog_rest_port and user-agent=anylog and log=false and topic=(
    name=!policy_id and
    policy=!policy_id
)>

:end-script:
end script

:terminate-scripts:
exit scripts

:test-policy-error:
echo "Invalid JSON format, cannot declare policy"
goto end-script

:sign-policy-error:
print "Failed to sign cluster policy"
goto terminate-scripts

:prepare-policy-error:
print "Failed to prepare member cluster policy for publishing on blockchain"
goto terminate-scripts

:declare-policy-error:
print "Failed to declare cluster policy on blockchain"
goto terminate-scripts

:policy-error:
print "Failed to publish policy for an unknown reason"
goto terminate-scripts


:msg-error:
echo "Failed to deploy MQTT process"
goto end-script





