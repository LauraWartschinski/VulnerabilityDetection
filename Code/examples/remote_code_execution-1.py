from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import list_route
from flask import escape

from .models import BoxDetails, RegisteredServices
from .serializers import BoxDetailsSerializer, RegisteredServicesSerializer

import common, sqlite3, subprocess, NetworkManager, os, crypt, pwd, getpass, spwd 

# fetch network AP details
nm = NetworkManager.NetworkManager
wlans = [d for d in nm.Devices if isinstance(d, NetworkManager.Wireless)]

def get_osversion():
    """
    PRETTY_NAME of your Titania os (in lowercase).
    """
    with open("/etc/os-release") as f:
        osfilecontent = f.read().split("\n")
        # $PRETTY_NAME is at the 5th position
        version = osfilecontent[4].split('=')[1].strip('\"')
        return version

def get_allconfiguredwifi():
    """
    nmcli con | grep 802-11-wireless
    """
    ps = subprocess.Popen('nmcli -t -f NAME,TYPE conn | grep 802-11-wireless', shell=True,stdout=subprocess.PIPE).communicate()[0]
    wifirows = ps.split('\n')
    wifi = []
    for row in wifirows:
        name = row.split(':')
        print(name)
        wifi.append(name[0])
    return wifi

def get_allAPs():
    """
    nmcli con | grep 802-11-wireless
    """
    ps = subprocess.Popen('nmcli -t -f SSID,BARS device wifi list', shell=True,stdout=subprocess.PIPE).communicate()[0]
    wifirows = ps.split('\n')
    wifi = []
    for row in wifirows:
        entry = row.split(':')
        print(entry)
        wifi.append(entry)
    return wifi
    # wifi_aps = []   
    # for dev in wlans:
    #     for ap in dev.AccessPoints:
    #         wifi_aps.append(ap.Ssid)
    # return wifi_aps

def add_user(username, password):
    encPass = crypt.crypt(password,"22")
    os.system("useradd -G docker,wheel -p "+encPass+" "+username)

def add_newWifiConn(wifiname, wifipass):
    print(wlans)
    wlan0 = wlans[0]
    print(wlan0)
    print(wifiname)
    # get selected ap as currentwifi
    for dev in wlans:
        for ap in dev.AccessPoints:
            if ap.Ssid == wifiname:
                currentwifi = ap
    print(currentwifi)
    # params to set password
    params = {
            "802-11-wireless": {
                "security": "802-11-wireless-security",
            },
            "802-11-wireless-security": {
                "key-mgmt": "wpa-psk",
                "psk": wifipass
            },
        }
    conn = nm.AddAndActivateConnection(params, wlan0, currentwifi)        

def delete_WifiConn(wifiap):
    """
    nmcli connection delete id <connection name>
    """
    ps = subprocess.Popen(['nmcli', 'connection','delete','id',wifiap], stdout=subprocess.PIPE)
    print(ps)

def edit_WifiConn(wifiname, wifipass):
    ps = subprocess.Popen(['nmcli', 'connection','delete','id',wifiname], stdout=subprocess.PIPE)
    print(ps)
    print(wlans)
    wlan0 = wlans[0]
    print(wlan0)
    print(wifiname)
    # get selected ap as currentwifi
    for dev in wlans:
        for ap in dev.AccessPoints:
            if ap.Ssid == wifiname:
                currentwifi = ap
    # params to set password
    params = {
            "802-11-wireless": {
                "security": "802-11-wireless-security",
            },
            "802-11-wireless-security": {
                "key-mgmt": "wpa-psk",
                "psk": wifipass
            },
        }
    conn = nm.AddAndActivateConnection(params, wlan0, currentwifi) 
    return       

@csrf_exempt
def handle_config(request):
    """
    List all code snippets, or create a new snippet.
    """ 
    if request.method == 'POST':
        action = request.POST.get("_action")
        print(action)
        if action == 'registerService':
            request_name = request.POST.get("name")
            request_address = request.POST.get("address")
            request_icon = request.POST.get("icon")
            print(request_name)
            print(request_address)
            print(request_icon)
            setServiceDetails = RegisteredServices.objects.get_or_create(name=request_name,address=request_address,icon=request_icon)
            return JsonResponse({"STATUS":"SUCCESS"}, safe=False)
        elif action == 'getSchema':
            schema = get_osversion()
            return JsonResponse({"version_info":schema}, safe=False)
        elif action == 'getIfConfigured':
            print(action)
            queryset = BoxDetails.objects.all()
            serializer = BoxDetailsSerializer(queryset, many=True)
            return JsonResponse(serializer.data, safe=False)
        elif action == 'loadDependencies':
            print(action)
            queryset = RegisteredServices.objects.all()
            serializer = RegisteredServicesSerializer(queryset, many=True)
            return JsonResponse(serializer.data, safe=False)
        elif action == 'getAllAPs':
            wifi_aps = get_allAPs()
            return JsonResponse(wifi_aps, safe=False)
        elif action == 'saveUserDetails':
            print(action)
            boxname = escape(request.POST.get("boxname"))
            username = escape(request.POST.get("username"))
            password = escape(request.POST.get("password"))
            print(username)
            add_user(username,password)
            setBoxName = BoxDetails(boxname=boxname)
            setBoxName.save()
            # connect to wifi ap user selected
            wifi_pass = request.POST.get("wifi_password")
            wifi_name = request.POST.get("wifi_ap")
            if len(wifi_name) > 0:
                add_newWifiConn(wifi_name,wifi_pass)
            return JsonResponse({"STATUS":"SUCCESS"}, safe=False)
        elif action == 'login':
            print(action)
            username = escape(request.POST.get("username"))
            password = escape(request.POST.get("password"))
            output=''
            """Tries to authenticate a user.
            Returns True if the authentication succeeds, else the reason
            (string) is returned."""
            try:
                enc_pwd = spwd.getspnam(username)[1]
                if enc_pwd in ["NP", "!", "", None]:
                    output = "User '%s' has no password set" % username
                if enc_pwd in ["LK", "*"]:
                    output = "account is locked"
                if enc_pwd == "!!":
                    output = "password has expired"
                # Encryption happens here, the hash is stripped from the
                # enc_pwd and the algorithm id and salt are used to encrypt
                # the password.
                if crypt.crypt(password, enc_pwd) == enc_pwd:
                    output = ''
                else:
                    output = "incorrect password"
            except KeyError:
                output = "User '%s' not found" % username
            if len(output) == 0:
                return JsonResponse({"username":username}, safe=False)
            else:
                return JsonResponse(output, safe=False)
        elif action == 'logout':
            print(action)
            username = request.POST.get("username")
            print(username+' ')
            queryset = User.objects.all().first()
            if username == queryset.username:
                return JsonResponse({"STATUS":"SUCCESS", "username":queryset.username}, safe=False)
        elif action == 'getDashboardCards':
            print(action)
            con = sqlite3.connect("dashboard.sqlite3")
            cursor = con.cursor()
            cursor.execute(common.Q_DASHBOARD_CARDS)
            rows = cursor.fetchall()
            print(rows)
            return JsonResponse(rows, safe=False)
        elif action == 'getDashboardChart':
            print(action)
            con = sqlite3.connect("dashboard.sqlite3")
            cursor = con.cursor()
            cursor.execute(common.Q_GET_CONTAINER_ID)
            rows = cursor.fetchall()
            print(rows)
            finalset = []
            for row in rows:
                cursor.execute(common.Q_GET_DASHBOARD_CHART,[row[0],])
                datasets = cursor.fetchall()
                print(datasets)
                data = {'container_name' : row[1], 'data': datasets}
                finalset.append(data)
            return JsonResponse(finalset, safe=False)
        elif action == 'getDockerOverview':
            print(action)
            con = sqlite3.connect("dashboard.sqlite3")
            cursor = con.cursor()
            cursor.execute(common.Q_GET_DOCKER_OVERVIEW)
            rows = cursor.fetchall()
            print(rows)
            finalset = []
            for row in rows:
                data = {'state': row[0], 'container_id': row[1], 'name': row[2],
                        'image': row[3], 'running_for': row[4],
                        'command': row[5], 'ports': row[6],
                        'status': row[7], 'networks': row[8]}
                finalset.append(data)
            return JsonResponse(finalset, safe=False)
        elif action == 'getContainerStats':
            print(action)
            con = sqlite3.connect("dashboard.sqlite3")
            cursor = con.cursor()
            cursor.execute(common.Q_GET_CONTAINER_ID)
            rows = cursor.fetchall()
            print(rows)
            finalset = []
            datasets_io = []
            datasets_mem = []
            datasets_perc = []
            for row in rows:
                datasets_io = []
                datasets_mem = []
                datasets_perc = []
                # values with % appended to them
                for iter in range(0,2):
                    cursor.execute(common.Q_GET_CONTAINER_STATS_CPU,[row[0],iter+1])
                    counter_val = cursor.fetchall()
                    datasets_perc.append(counter_val)
                # values w/o % appended to them
                for iter in range(2,4):
                    cursor.execute(common.Q_GET_CONTAINER_STATS,[row[0],iter+1])
                    counter_val = cursor.fetchall()
                    datasets_mem.append(counter_val)
                # values w/o % appended to them
                for iter in range(4,8):
                    cursor.execute(common.Q_GET_CONTAINER_STATS,[row[0],iter+1])
                    counter_val = cursor.fetchall()
                    datasets_io.append(counter_val)
                data = {'container_id': row[0], 'container_name' : row[1], 'data_io': datasets_io, 'data_mem': datasets_mem, 'data_perc': datasets_perc}
                finalset.append(data)
            return JsonResponse(finalset, safe=False)
        elif action == 'getThreads':
            print(action)
            rows = []
            ps = subprocess.Popen(['top', '-b','-n','1'], stdout=subprocess.PIPE).communicate()[0]
            processes = ps.decode().split('\n')
            # this specifies the number of splits, so the splitted lines
            # will have (nfields+1) elements
            nfields = len(processes[0].split()) - 1
            for row in processes[4:]:
                rows.append(row.split(None, nfields))
            return JsonResponse(rows, safe=False)
        elif action == 'getContainerTop':
            print(action)
            con = sqlite3.connect("dashboard.sqlite3")
            cursor = con.cursor()
            cursor.execute(common.Q_GET_CONTAINER_ID)
            rows = cursor.fetchall()
            resultset = []
            for i in rows:
                data = {}
                datasets = []
                ps = subprocess.Popen(['docker', 'top',i[0]], stdout=subprocess.PIPE).communicate()[0]
                processes = ps.decode().split('\n')
                # this specifies the number of splits, so the splitted lines
                # will have (nfields+1) elements
                nfields = len(processes[0].split()) - 1
                for p in processes[1:]:
                    datasets.append(p.split(None, nfields))
                data = {'container_id': i[0], 'container_name' : i[1], 'data': datasets}
                resultset.append(data)
            return JsonResponse(resultset, safe=False)
        elif action == 'getSettings':
            print(action)
            ps = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = ps.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps}], safe=False)
        elif action == 'deleteUser':
            print(action)
            username = escape(request.POST.get("user"))
            ps = subprocess.Popen(['userdel', username], stdout=subprocess.PIPE).communicate()
            fetchusers = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = fetchusers.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps, 'reqtype': 'deleteuser', 'endpoint': username}], safe=False)
        elif action == 'addNewUser':
            print(action)
            username = escape(request.POST.get("username"))
            password = escape(request.POST.get("password"))
            add_user(username,password)
            fetchusers = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = fetchusers.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps, 'reqtype': 'adduser', 'endpoint': username}], safe=False)
        elif action == 'addWifi':
            print(action)
            # connect to wifi ap user selected
            wifi_pass = escape(request.POST.get("wifi_password"))
            wifi_name = request.POST.get("wifi_ap")
            if len(wifi_name) > 0:
                add_newWifiConn(wifi_name,wifi_pass)
            fetchusers = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = fetchusers.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps, 'reqtype': 'addwifi', 'endpoint': wifi_name}], safe=False)
        elif action == 'deleteWifi':
            print(action)
            # connect to wifi ap user selected
            wifi_name = request.POST.get("wifi")
            delete_WifiConn(wifi_name)
            fetchusers = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = fetchusers.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps, 'reqtype': 'deletewifi', 'endpoint': wifi_name}], safe=False)
        elif action == 'editWifi':
            print(action)
            # connect to wifi ap user selected
            wifi_name = request.POST.get("wifi_ap")
            wifi_pass = escape(request.POST.get("wifi_password"))
            edit_WifiConn(wifi_name,wifi_pass)
            fetchusers = subprocess.Popen(['grep', '/etc/group','-e','docker'], stdout=subprocess.PIPE).communicate()[0].split('\n')[0]
            # sample ps 
            # docker:x:992:pooja,asdasd,aaa,cow,dsds,priya,asdas,cowwwwww,ramm,asdasdasdasd,asdasdas,adam,run
            userlist = fetchusers.split(':')[3].split(',')
            configuredwifi = get_allconfiguredwifi()
            wifi_aps = get_allAPs()
            return JsonResponse([{'users':userlist,'wifi':configuredwifi,'allwifiaps':wifi_aps, 'reqtype': 'editwifi', 'endpoint': wifi_name}], safe=False)
        return JsonResponse(serializer.errors, status=400)

def index(request):
    return render(request, 'index.html')

class BoxDetailsViewSet(viewsets.ModelViewSet):
    queryset = BoxDetails.objects.all()
    serializer_class = BoxDetailsSerializer

class RegisteredServicesViewSet(viewsets.ModelViewSet):
    queryset = RegisteredServices.objects.all()
    serializer_class = RegisteredServicesSerializer    


