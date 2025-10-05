import json, os

IN = 'output/messier_skymap_8k_hotspots.json'
OUT = 'output/messier_hotspots_leaflet.json'

def px_to_radec(x,y,width=8192,height=4096):
    ra = (x / width) * 360.0
    dec = 90.0 - (y / height) * 180.0
    return ra, dec

def radec_to_latlng(ra,dec):
    lat = dec
    lng = ra - 180.0
    return lat, lng

if __name__=='__main__':
    if not os.path.exists(IN):
        print('Hotspots input not found:', IN)
        raise SystemExit(1)
    hs = json.load(open(IN,'r',encoding='utf-8'))
    out = []
    for h in hs:
        cx, cy = h['center_px']
        ra, dec = px_to_radec(cx, cy)
        lat, lng = radec_to_latlng(ra, dec)
        bbox = h['bbox_px']
        # convert bbox corners
        ra0, dec0 = px_to_radec(bbox[0], bbox[1])
        ra1, dec1 = px_to_radec(bbox[2], bbox[3])
        lat0, lng0 = radec_to_latlng(ra0, dec0)
        lat1, lng1 = radec_to_latlng(ra1, dec1)
        out.append({
            'id': h['id'],
            'name': h.get('name'),
            'center': {'lat': lat, 'lng': lng},
            'bbox': {'south': min(lat0,lat1), 'north': max(lat0,lat1), 'west': min(lng0,lng1), 'east': max(lng0,lng1)}
        })
    os.makedirs('output', exist_ok=True)
    json.dump(out, open(OUT,'w',encoding='utf-8'), indent=2)
    print('Wrote', OUT)
