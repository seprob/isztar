#!/usr/bin/env python

import subprocess, json, requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

constants = json.loads(open("constants.json").read())
variable = requests.get("https://"
                        + constants["hostname"]
                        + "/v2/"
                        + "_catalog",
                        verify = False,
                        auth = ('', ''))
repositories = variable.json()
iterator1 = 0

# Dla kazdego repozytorium.

while iterator1 < len(repositories["repositories"]):
    if repositories["repositories"][iterator1] in constants["repositories_to_leave"]:
       iterator1 += 1

       continue

    print "[*] Repozytorium: \"" + repositories["repositories"][iterator1] + "\""

    variable = requests.get("https://"
                            + constants["hostname"]
                            + "/v2/"
                            + repositories["repositories"][iterator1]
                            + "/tags/list",
                            verify = False,
                            auth = ('', ''))

    tags = variable.json()  
    
    if tags["tags"] is None:
        iterator1 += 1

        continue
    
    sorted_tags = tags["tags"] # Przypisz jako liste.

    sorted_tags.sort() # Posortuj.

    # Wyciaganie danych na temat utworzenia kontenera.

    iterator2 = 0
    tag_blobs = {} # Slownik gdzie kluczem klucz kropelka (blob), a jako wartosc znacznik kontenera.

    while iterator2 < len(sorted_tags):
        headers = {
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
        }

        variable = requests.get("https://"
                                + constants["hostname"]
                                + "/v2/"
                                + repositories["repositories"][iterator1]
                                + "/"
                                + "manifests/"
                                + sorted_tags[iterator2],
                                headers = headers,
                                verify = False,
                                auth = ('', ''))
        blob_digest = json.loads(variable.text)["config"]["digest"]

        if blob_digest: # Sprawdz czy informacje zostaly zwrocone.
            digest_blob = requests.get("https://"
                                       + constants["hostname"]
                                       + "/v2/"
                                       + repositories["repositories"][iterator1]
                                       + "/blobs"
                                       + "/"
                                       + blob_digest, 
                                       verify = False, 
                                       auth = ('', ''))
            
            digest_blob = digest_blob.text

            if "Internal Server Error" in digest_blob:
               iterator2 += 1

               continue

            digest_blob = json.loads(digest_blob)

            # Sprawdz czy zwrocono informacje kiedy obraz zostal stworzony.

            if "created" in digest_blob:
                tag_blobs[digest_blob["created"]] = sorted_tags[iterator2] # Przypisz jako klucz kropelke (blob), a jako wartosc znacznik kontenera.

        iterator2 += 1

    tag_blob_sorted = sorted(tag_blobs) # Posortuj.

    iterator2 = 0

    # Dla kazdego znacznika zostaw podana liczbe obrazow.

    while iterator2 < (len(tag_blob_sorted) - constants["no_images_to_left"]):
        if tag_blobs[tag_blob_sorted[iterator2]] == "latest":
            iterator2 += 1

            continue

        # Sprawdz czy na liscie kluczy wersji kontenerow, ktore zostawic jest aktualnie przetwarzane repozytorium.

        if repositories["repositories"][iterator1] in constants["containers_to_leave"].keys():
            # Pomin znacznik (wersje), ktory jest w stalych.

            if tag_blobs[tag_blob_sorted[iterator2]] in constants["containers_to_leave"][repositories["repositories"][iterator1]]:
                iterator2 += 1

                continue

        print "[*] Znacznik do usuniecia: \"" + tag_blobs[tag_blob_sorted[iterator2]] + "\""

        # Wyciagnij skrot SHA256.

        headers = {
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
        }

        response = requests.get("https://"
                                + constants["hostname"]
                                + "/v2/"
                                + repositories["repositories"][iterator1]
                                + "/"
                                + "manifests/"
                                + tag_blobs[tag_blob_sorted[iterator2]],
                                headers = headers,
                                verify = False,
                                auth = ('', ''))

        sha256_digest = response.headers['docker-content-digest']

        if sha256_digest: # Sprawdz czy informacje zostaly zwrocone w tablicy.
            # Usun znacznik.

            print ("[*] Wywolanie usuwajace: \""
                   + "curl -k -u "
                   + constants["user"]
                   + ":"
                   + constants["password"]
                   + " -X DELETE "
                   + constants["hostname"]
                   + "/v2/"
                   + repositories["repositories"][iterator1]
                   + "/"
                   + "manifests/"
                   + sha256_digest.rstrip()
                   + "\"").rstrip()

            url = ("https://"
                   + constants["hostname"]
                   + "/v2/"
                   + repositories["repositories"][iterator1]
                   + "/"
                   + "manifests/"
                   + sha256_digest)

            url = url.rstrip() # Usun biale znaki.

            var = requests.delete(url, verify = False, auth = (constants["user"], constants["password"]))

        iterator2 += 1

    iterator1 += 1

    print "" # Nowa linia.
