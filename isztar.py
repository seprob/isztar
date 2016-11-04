#!/usr/bin/env python

import subprocess, json, requests

constants = json.loads(open("constants.json").read())
variable = subprocess.Popen("curl -k -u "
                            + constants["user"]
                            + ":"
                            + constants["password"]
                            + " -X GET "
                            + constants["hostname"]
                            + "/_catalog",
                            stdout = subprocess.PIPE,
                            shell = True,
                            stderr = subprocess.PIPE) # Pobierz aktualny katalog repozytoriow.
repositories_json = variable.stdout.read() # Przypisz do zmiennej.
repositories = json.loads(repositories_json) # Zamien na JSON-a.
iterator1 = 0

# Dla kazdego repozytorium.

while iterator1 < len(repositories["repositories"]):
    if "smart" in repositories["repositories"][iterator1]: # Pomin repozytoria, ktore zawieraja "smart" w nazwie (SmartOffice).
        iterator1 += 1

        continue

    print "REPOZYTORIUM: \"" + repositories["repositories"][iterator1] + "\""

    variable = subprocess.Popen("curl -k -u "
                                + constants["user"]
                                + ":"
                                + constants["password"]
                                + " -X GET "
                                + constants["hostname"]
                                + "/"
                                + repositories["repositories"][iterator1]
                                + "/tags/list",
                                stdout = subprocess.PIPE,
                                shell = True,
                                stderr = subprocess.PIPE) # Pobierz znaczniki dla danego repozytorium.
    tags_json = variable.stdout.read() # Przypisz do zmiennej.
    tags = json.loads(tags_json) # Zamien na JSON-a.
    sorted_tags = tags["tags"] # Przypisz jako liste.

    sorted_tags.sort() # Posortuj.

    # Wyciaganie danych na temat utworzenia kontenera.

    iterator2 = 0
    tag_blobs = {} # Slownik gdzie kluczem klucz kropelka (blob), a jako wartosc znacznik kontenera.

    while iterator2 < len(sorted_tags):
        variable = subprocess.Popen('curl -k -u '
                                    + constants["user"]
                                    + ":"
                                    + constants["password"]
                                    + ' -H "Accept: application/vnd.docker.distribution.manifest.v2+json" -D - '
                                    + constants["hostname"]
                                    + "/"
                                    + repositories["repositories"][iterator1]
                                    + "/"
                                    + "manifests/"
                                    + sorted_tags[iterator2]
                                    + " | grep digest",
                                    stdout = subprocess.PIPE,
                                    shell = True,
                                    stderr = subprocess.PIPE) # Wyciagnij skrot kropelki ("blob digest").
        blob_digest = variable.stdout.read().split() # Wczytaj dane i stworz tablice.

        if blob_digest: # Sprawdz czy informacje zostaly zwrocone.
            blob_digest[1] = blob_digest[1][1:-1] # Pozbadz sie cudzyslowow.

            variable = subprocess.Popen("curl -k -u "
                                        + constants["user"]
                                        + ":"
                                        + constants["password"]
                                        + " -sS -X GET "
                                        + constants["hostname"]
                                        + "/"
                                        + repositories["repositories"][iterator1]
                                        + "/blobs"
                                        + "/"
                                        + blob_digest[1],
                                        stdout = subprocess.PIPE,
                                        shell = True,
                                        stderr = subprocess.PIPE) # Pobierz kropellke (blob).

            digest_blob = json.loads(variable.stdout.read())

            tag_blobs[digest_blob["created"]] = sorted_tags[iterator2] # Przypisz jako klucz kropelke (blob), a jako wartosc nacznik kontenera.

        iterator2 += 1

    tag_blob_sorted = sorted(tag_blobs) # Posortuj.

    iterator2 = 0

    # Dla kazdego znacznika zostaw podana liczbe obrazow.

    while iterator2 < (len(tag_blob_sorted) - constants["no_images_to_left"]):
        if tag_blobs[tag_blob_sorted[iterator2]] == "latest":
            iterator2 += 1

            continue

        print "Znacznik: \"" + tag_blobs[tag_blob_sorted[iterator2]] + "\""

        # Wyciagnij skrot SHA256.

        variable = subprocess.Popen('curl -k -u '
                                    + constants["user"]
                                    + ":"
                                    + constants["password"]
                                    + ' -H "Accept: application/vnd.docker.distribution.manifest.v2+json" -D - '
                                    + constants["hostname"]
                                    + "/"
                                    + repositories["repositories"][iterator1]
                                    + "/"
                                    + "manifests/"
                                    + tag_blobs[tag_blob_sorted[iterator2]]
                                    + " | grep Docker-Content-Digest",
                                    stdout = subprocess.PIPE,
                                    shell = True,
                                    stderr = subprocess.PIPE)
        sha256_digest = variable.stdout.read().partition(": ")[2]

        if sha256_digest: # Sprawdz czy informacje zostaly zwrocone w tablicy.
            # Usun znacznik.

            print ("Wywolanie: \""
                   + "curl -k -u "
                   + constants["user"]
                   + ":"
                   + constants["password"]
                   + " -X DELETE "
                   + constants["hostname"]
                   + "/"
                   + repositories["repositories"][iterator1]
                   + "/"
                   + "manifests/"
                   + sha256_digest.rstrip()
                   + "\"").rstrip()

            url = (constants["hostname"]
                   + "/"
                   + repositories["repositories"][iterator1]
                   + "/"
                   + "manifests/"
                   + sha256_digest)

            url = url.rstrip() # Usun biale znaki.

            var = requests.delete(url, verify = False, auth = (constants["user"], constants["password"]))

            print "Zwrocono status o kodzie: " + var.status_code

        iterator2 += 1

    iterator1 += 1

    print "" # Nowa linia.