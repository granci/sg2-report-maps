import requests

if __name__ == '__main__':
    output_image = 'test.png'
    service_url = 'http://127.0.0.1:8000'
    request_params = {
        'lat': 33.951904,
        'lon': -6.804657,
        'countryCode': 'MA',
        # 'type': 'site_location',
        'type': 'world_map',
        'whratio': 1
    }
    print "Making request to '{}'!".format(service_url)
    response = requests.get(service_url, params=request_params)
    if response.headers.get('content-type') == "image/png":
        with open(output_image, 'wb') as out_file:
            # shutil.copyfileobj(response.raw, out_file)
            out_file.write(response.content)
            print "URL content saved to '{}'!".format(output_image)
    else:
        print(response.text)