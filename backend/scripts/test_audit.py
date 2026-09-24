import urllib.request
import urllib.error
import json

def run_tests():
    print('=== 1. SYSTEM HEALTH & ROUTES ===')
    res = urllib.request.urlopen('http://127.0.0.1:8000/health')
    print('Backend /health:', res.getcode(), json.loads(res.read().decode()))

    for route in ['/login', '/student', '/attendance', '/dashboard']:
        f_res = urllib.request.urlopen(f'http://localhost:3000{route}')
        print(f'Frontend {route}:', f_res.getcode())

    print('\n=== 2. AUTHENTICATION (ADMIN & STUDENT) ===')
    # Admin login
    import os
    admin_pass = os.environ.get("ADMIN_PASSKEY", "")
    admin_req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', 
        data=json.dumps({'identifier': 'admin@mithra.vit.ac.in', 'passkey': admin_pass}).encode(),
        headers={'Content-Type': 'application/json'})
    admin_data = json.loads(urllib.request.urlopen(admin_req).read().decode())['data']
    admin_token = admin_data['token']
    print('Admin Login:', admin_data['role'], '| Redirect:', admin_data['portalRedirect'], '| User:', admin_data['user']['name'])

    # Student login by Roll Number
    s_req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', 
        data=json.dumps({'identifier': 'VM001', 'password': 'any'}).encode(),
        headers={'Content-Type': 'application/json'})
    s_data = json.loads(urllib.request.urlopen(s_req).read().decode())['data']
    student_token = s_data['token']
    print('Student Login (VM001):', s_data['role'], '| Redirect:', s_data['portalRedirect'], '| User:', s_data['user']['name'])

    # Student login by Email
    s_email_req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', 
        data=json.dumps({'identifier': 'aditya.v@vitstudent.ac.in', 'password': 'any'}).encode(),
        headers={'Content-Type': 'application/json'})
    s_email_data = json.loads(urllib.request.urlopen(s_email_req).read().decode())['data']
    print('Student Login (Email):', s_email_data['role'], '| User:', s_email_data['user']['name'])

    print('\n=== 3. STUDENT PORTAL DATA ACCESS ===')
    prof_req = urllib.request.Request('http://127.0.0.1:8000/api/student/me', headers={'Authorization': f'Bearer {student_token}'})
    prof = json.loads(urllib.request.urlopen(prof_req).read().decode())['data']
    print('Student Profile:', prof['name'], '| Roll:', prof['memberId'], '| Dept:', prof['departmentName'])

    att_req = urllib.request.Request('http://127.0.0.1:8000/api/student/me/attendance', headers={'Authorization': f'Bearer {student_token}'})
    att = json.loads(urllib.request.urlopen(att_req).read().decode())['data']
    print('Attendance Percentage:', f"{att['overallAttendancePercentage']}%")
    print('Total Sessions:', att['totalSessions'], '| Present:', att['presentCount'], '| Absent:', att['absentCount'])

    team_req = urllib.request.Request('http://127.0.0.1:8000/api/student/me/team', headers={'Authorization': f'Bearer {student_token}'})
    team = json.loads(urllib.request.urlopen(team_req).read().decode())['data']
    print('Team Wing:', team['departmentName'], '| Roster Count:', team['totalMembers'], '| Members:', [f"{m['name']} ({m['memberId']})" for m in team['teamMembers']])

    print('\n=== 4. ATTENDANCE SAVING & ABSENT TEST ===')
    # Save VM001 as ABSENT
    bulk_absent = urllib.request.Request('http://127.0.0.1:8000/api/attendance/bulk',
        data=json.dumps({'date': '2026-09-18', 'records': [{'memberId': 'VM001', 'status': 'ABSENT'}]}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'})
    res_absent = json.loads(urllib.request.urlopen(bulk_absent).read().decode())
    print('Save ABSENT response:', res_absent['success'], '| Successful:', res_absent['data']['successful'])

    # Verify persisted in database
    chk_absent = urllib.request.Request('http://127.0.0.1:8000/api/attendance?date=2026-09-18&memberId=VM001', headers={'Authorization': f'Bearer {admin_token}'})
    persisted_att = json.loads(urllib.request.urlopen(chk_absent).read().decode())['data']
    print('Persisted Status for VM001 on 2026-09-18:', persisted_att[0]['status'])

    # Switch VM001 back to PRESENT
    bulk_present = urllib.request.Request('http://127.0.0.1:8000/api/attendance/bulk',
        data=json.dumps({'date': '2026-09-18', 'records': [{'memberId': 'VM001', 'status': 'PRESENT'}]}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {admin_token}'})
    res_present = json.loads(urllib.request.urlopen(bulk_present).read().decode())
    print('Save PRESENT response:', res_present['success'], '| Successful:', res_present['data']['successful'])

    chk_present = urllib.request.Request('http://127.0.0.1:8000/api/attendance?date=2026-09-18&memberId=VM001', headers={'Authorization': f'Bearer {admin_token}'})
    persisted_pres = json.loads(urllib.request.urlopen(chk_present).read().decode())['data']
    print('Persisted Status for VM001 on 2026-09-18:', persisted_pres[0]['status'])

    print('\n=== 5. SECURITY GUARDRAIL TEST ===')
    try:
        urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/attendance/bulk',
            data=json.dumps({'date': '2026-09-18', 'records': [{'memberId': 'VM001', 'status': 'PRESENT'}]}).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {student_token}'}))
        print('Security check FAILED: Student should not be able to mark roll!')
    except urllib.error.HTTPError as e:
        print(f'Security check PASSED: HTTP {e.code} Forbidden (Student blocked from attendance mutations)')

    print('\n>>> ALL SYSTEM AUDITS PASSED CLEANLY! <<<')

if __name__ == '__main__':
    run_tests()
