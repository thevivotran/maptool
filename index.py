from flask import (Flask, render_template, request)
import requests
import bs4
import math

app = Flask(__name__)

def getWay(changeset):
    f = requests.get('https://www.openstreetmap.org/api/0.6/changeset/{}/download'.format(changeset))
    tree = bs4.BeautifulSoup(f.text, features="html.parser")
    ways = tree.find_all('way')
    way_ids = []
    for way in ways:
        way_ids.append(way['id'])
    return way_ids

def lengthCalculate(lat1, lat2, lon1, lon2):
    R = 6378.137
    dLat = lat2 * math.pi / 180 - lat1 * math.pi / 180
    dLon = lon2 * math.pi / 180 - lon1 * math.pi / 180
    a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180) * math.cos(lat2 * math.pi / 180) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d

def getLength(way_id):
    f = requests.get('https://www.openstreetmap.org/api/0.6/way/{}'.format(way_id))
    tree = bs4.BeautifulSoup(f.text, features="html.parser")
    nds = tree.find_all('nd')
    node_ids = []
    for n in nds:
        node_ids.append(n['ref'])
    nattrbs = []
    for node in node_ids:
        f = requests.get('https://www.openstreetmap.org/api/0.6/node/{}'.format(node))
        tree = bs4.BeautifulSoup(f.text, features="html.parser")
        nattrbs.append({'node': node,
                        'lat': float(tree.find('node')['lat']),
                        'long': float(tree.find('node')['lon'])})
    totalLength = 0
    for i in range(len(nattrbs) - 1):
        couple_value = nattrbs[i:i+2]
        totalLength = totalLength + lengthCalculate(couple_value[0]['lat'],
                                                    couple_value[1]['lat'],
                                                    couple_value[0]['long'],
                                                    couple_value[1]['long'])
    return totalLength

"""
@app.route('/<int:changeset>')
def input_changeset(changeset):
    wayids = getWay(changeset)
    return render_template('index.html', wayids=wayids)
"""

@app.route('/')
def welcome():
    return render_template('base.html')

@app.route('/ukmcal', methods=('GET', 'POST'))
def input():
    return render_template('ukmcal.html')

@app.route('/ukmcal/results', methods=('GET', 'POST'))
def result():
    results = []
    changeset_input = request.form['changesets']
    if changeset_input.count(',') != 0:
        changesets = changeset_input.split(',')
        for changeset in changesets:
            waysLength = 0
            ways = getWay(changeset)
            for way in ways:
                waysLength += getLength(way)
            if waysLength == 0:
                waysLength = 0.2
            results.append({'changeset': changeset,
                            'ways':' '.join(ways),
                            'ukm':round(waysLength, 2)})
    else:
        waysLength = 0
        ways = getWay(int(changeset_input))
        for way in ways:
            waysLength += getLength(way)
        if waysLength == 0:
            waysLength = 0.2
        results.append({'changeset':changeset_input,
                        'ways':' '.join(ways),
                        'ukm':round(waysLength, 2)})
    return render_template('results.html', results=results)

@app.route('/geofence')
def geofence():
    return render_template('geofence.html')

@app.route('/geofence/reversed', methods=['POST'])
def reversed():
    input_value = request.form.get('input_value')
    def reverse_geofence(input):
        ls = input.split(' ')
        rs = []
        for coordinate in ls:
            if coordinate.count(',') == 1:
                rs.append(coordinate.replace(',', ''))
            else:
                rs.append(coordinate)
        rs.reverse()
        return ', '.join(rs)
    return render_template('reversed.html', result=reverse_geofence(input_value))

app.run(debug=True)