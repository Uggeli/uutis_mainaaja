from tqdm import tqdm
from multiprocessing import Process, Queue, cpu_count
from louhija4 import Louhija
import requests, bs4, re, os


def main():
    Louhija('testi', 'testi')
    yhtiot = hae_listatut_yhtiot()

    jono = Queue()
    for osake, yhtio in yhtiot.items():
        jono.put([osake, yhtio[0]])

    threadit = cpu_count()
    prosessit = []

    for threadi in range(threadit):
        threadi = Process(target=worker, args=(jono, ))
        threadi.daemon = True
        threadi.start()
        prosessit.append(threadi)

    for threadi in prosessit:
        threadi.join()


def worker(jono):
    while not jono.empty():
        duuni = jono.get()
        # os.system('cmd')
        Louhija(duuni[1], duuni[0])


def hae_listatut_yhtiot():
    resp = requests.get('http://www.nasdaqomxnordic.com/shares/listed-companies/helsinki')
    soup = bs4.BeautifulSoup(resp.text, 'lxml')
    table = soup.find('table', {'class': 'tablesorter'})
    yhtiot = {}
    lyhenteet = []
    linkit = []
    nimet = []

    for row in table.findAll('tr')[1:]:
        lyhenne = row.findAll('td')[1:2]
        lyhenne = str(lyhenne)
        lyhenne = re.findall(r">(.*)<", lyhenne)
        lyhenne = re.sub(r'\[\'', '', str(lyhenne))
        lyhenne = re.sub(r'\'\]', '', str(lyhenne))
        lyhenteet.append(lyhenne)

        for linkki in row.findAll('a', href=True):
            nimi = re.findall(r'name=(.*)\"', str(linkki))
            linkki = re.findall(r'/shares.*\"', str(linkki))
            if len(linkki) > 0:
                linkki = re.sub(r'\"', '', str(linkki))
                linkki = re.sub(r'\[\'', '', str(linkki))
                linkki = re.sub(r'\'\]', '', str(linkki))
                linkit.append(linkki)
            if len(nimi) > 0:
                nimi = re.sub(r'\[\'', '', str(nimi))
                nimi = re.sub(r'\'\]', '', str(nimi))
                nimet.append(nimi)

    for lyhenne, nimi, linkki in zip(lyhenteet, nimet, linkit):
        yhtiot[str(lyhenne)] = [nimi, linkki]
    return yhtiot

if __name__ == "__main__":
    main()
