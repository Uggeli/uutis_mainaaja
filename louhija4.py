from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import re, time, os, requests, zipfile
import bs4
from pathlib import Path
from tqdm import tqdm


class Louhija():
    def __init__(self, yhtio, osake):
        if yhtio == 'testi' and osake == 'testi':
            self.yhtio = yhtio
            self.osake = osake
            self.tarkista_kansiot('kaikki')
            self.tarkista_driver()
            print('testataan')
        else:
            self.yhtio = yhtio
            self.osake = osake
            self.tarkista_kansiot('kaikki')
            self.tarkista_driver()
            self.kaynnista_driver()
            self.hae_historia_data(self.driver)
            self.hae_kauppalehdesta(self.driver)
            self.hae_ylesta(self.driver)
            self.lopeta_driver()
            print(self.yhtio, 'Valmis')

    def hae_historia_data(self, driver):

        if self.osake == 'ASPO':
            self.osake = 'Aspo Oyj'

        driver.get('http://www.nasdaqomxnordic.com/osakkeet/historiallisetkurssitiedot')
        elem = driver.find_element_by_xpath('//*[@id="instSearchHistorical"]')
        alku = driver.find_element_by_xpath('//*[@id="FromDate"]')
        lataa = driver.find_element_by_xpath('//*[@id="exportExcel"]')

        alku.clear()
        alku.send_keys('2000-01-01')
        alku.send_keys(Keys.ENTER)
        elem.clear()
        elem.send_keys(self.osake)
        time.sleep(2)
        euro = driver.find_element_by_partial_link_text('(EUR)')
        euro.click()
        time.sleep(3)
        lataa.click()   
        time.sleep(2)

        #haxx korjaukset
        if self.osake == 'Aspo Oyj':
            self.osake = 'ASPO'

        if self.osake == 'NDA FI':
            self.osake = 'NDA-FI'

        valmis = False        
        while valmis == False:
            for tiedosto in os.listdir(Path(self.historia)):
                if self.osake in tiedosto and tiedosto.endswith('.csv'):
                    valmis = True

    def tarkista_driver(self):
        if not Path(self.chromedriver_exe).is_file():
            print('Driveriä ei löytynyt ladataan')
            response = requests.get('https://chromedriver.storage.googleapis.com/77.0.3865.40/chromedriver_win32.zip')
            with open(self.chromedriver_kansio + 'chromedriver_win32.zip','wb') as w:
                for data in tqdm(response.iter_content(), 'ladattu', len(response.content), ncols=100):
                    w.write(data)

            with zipfile.ZipFile(self.chromedriver_kansio + 'chromedriver_win32.zip', 'r') as z:
                z.extractall(self.chromedriver_kansio)

    def tarkista_kansiot(self, moodi):
        self.kansiot_tarkistettu = []

        try:
            os.mkdir('/finanssi/')
        except FileExistsError:
            pass
        if moodi == 'kaikki':

            #tarkista että kansiot löytyvät
            kansiot = [('finanssi/data_kansio/' + self.yhtio + '/uutiset/'), # Uutiset [0]
                       ('finanssi/data_kansio/' + self.yhtio + '/featuret/'),   # Featuret[1]
                       ('finanssi/data_kansio/' + self.yhtio + '/historia/'),   # Historia[2]
                       ('finanssi/data_kansio/' + self.yhtio + '/tulos/'),      # Tulos   [3]
                       './finanssi/driver/', # Driver  [4]  
                       'finanssi/data_kansio/' + self.yhtio]

            for kansio in kansiot:
                try:
                    os.makedirs(kansio)
                except FileExistsError:
                    pass
                self.kansiot_tarkistettu.append(str(Path(kansio).resolve()))

            for kansio in self.kansiot_tarkistettu:
                print(kansio)

                self.uutiset = self.kansiot_tarkistettu[0]
                self.featuret = self.kansiot_tarkistettu[1]
                self.historia = self.kansiot_tarkistettu[2]
                self.tulos = self.kansiot_tarkistettu[3]
                self.chromedriver_exe = self.kansiot_tarkistettu[4] + '/chromedriver.exe'
                self.chromedriver_kansio = self.kansiot_tarkistettu[4]
                self.data_kansio = self.kansiot_tarkistettu[5]

        if moodi == 'driver':
            self.chromedriver_exe = str(Path('finanssi/driver/chromedriver.exe').resolve())
            self.chromedriver_kansio = str(Path('finanssi/driver/').resolve())
            print(self.chromedriver_exe)

    def kaynnista_driver(self):
        profiili = webdriver.ChromeOptions()
        prefs = {"profile.default_content_settings.popups":0,
                        "download.default_directory": self.historia,
                        "download.prompt_for_download": False,    
                        "directory_upgrade": True}
        profiili.add_experimental_option("prefs",prefs)
        # try:
        print(str(Path(self.chromedriver_kansio + '/3.0.13_0.crx')))
        # profiili.add_extension(str(Path(self.chromedriver_kansio + '/3.0.13_0.crx')))
            # profiili.add_argument('load-extension='(self.chromedriver_kansio + '/3.0.13_9.crx'))
        # except:
        #     print('ei toiminu')
        #     pass
        #profiili.add_argument('--disable-extensions')
        profiili.add_argument('window-size=1200x600')
        # profiili.add_argument('--headless')
        profiili.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(executable_path=self.chromedriver_exe,options=profiili)
        
    def hae_ylesta(self,driver):
        sivu = r'https://haku.yle.fi/?language=fi&query='+ self.yhtio + r'&type=article&uiLanguage=fi'       
        driver.get(sivu)
        time.sleep(1)        
        source = driver.page_source
        soup = bs4.BeautifulSoup(source, 'lxml')
        lisaa = True
        linkit = []
        sivut_linkit_haettu = []
        while lisaa:
            sivut_linkit_haettu.append(driver.current_url)
            time.sleep(1)
            for linkki in soup.find_all('a'):
                if re.search('/uutiset/\d',str(linkki.get('href', None))):
                    linkit.append(linkki.get('href', None))
            print(len(linkit))
            try:
                driver.find_elements_by_css_selector('.fyIiTz')[-1].click()
            except Exception as e:
                # print(e)
                lisaa = False
            for haettu in sivut_linkit_haettu:
                if driver.current_url in haettu:
                    lisaa = False

        uutiset_haettu = []

        for linkki in linkit:
            for i in uutiset_haettu:
                if linkki not in i:
                    time.sleep(1)
                    driver.get(linkki)
                    artikkeli = []
                    try:
                        otsikko = driver.find_element_by_css_selector('.yle__article__heading--h1').text
                        time_stamp = driver.find_element_by_class_name("yle__article__date--published").text
                        kappaleet = driver.find_elements_by_class_name("yle__article__paragraph")
                    except Exception as e:
                        print(e)
                        input('tarkista')
                        pass
                    for kappale in kappaleet:
                        artikkeli.append(kappale.text)
                    self.kirjoita_levylle('uutinen',otsikko,time_stamp,artikkeli)
                    uutiset_haettu.append(linkki)

    def hae_kauppalehdesta(self, driver):
        sivu = 'https://www.kauppalehti.fi/haku/uutiset/' + self.yhtio
        print(sivu)
        self.driver.get(sivu)
        time.sleep(2)
        while True:
            print('odottaa pop uppia')
            try:
                driver.find_element_by_xpath('//*[@id="alma-data-policy-banner__accept-cookies-only"]').click()
                break
            except Exception as e:
                # print(e)
                pass
            
        lisaa = True
        while lisaa:
            time.sleep(2)
            try:
                nappi = driver.find_element_by_css_selector('.gLjshF')
                print('löytyi lisää')
                time.sleep(5)
                nappi.click()
            except:
                print('loppu')
                lisaa = False
                pass

        source = self.driver.page_source
        soup = bs4.BeautifulSoup(source,'lxml')

        linkit = [str(linkki.get('href',None)) for linkki in soup.find_all('a') 
                    if r'/uutiset/' in str(linkki.get('href',None)) and
                    'www' not in str(linkki.get('href',None)) and 
                    'haku' not in str(linkki.get('href',None))]

        #debuggausta:
        # input('tulostetaan linkit')
        # for linkki in linkit:
        #     print(linkki)
        # input(' . ')
        
        for linkki in linkit:
            driver.delete_all_cookies()
            time.sleep(1)
            try:
                driver.get('https://www.kauppalehti.fi' + linkki)
                otsikko = driver.find_element_by_css_selector('.gDrlGa').text            
                kappaleet = driver.find_elements_by_css_selector(".sc-1kqvxer-0")            
                time_stamp = driver.find_element_by_css_selector(".sc-1paerc3-0").text            
                artikkeli = []
                for kappale in kappaleet:                      
                    artikkeli.append(kappale.text)

                self.kirjoita_levylle('uutinen',otsikko,time_stamp,artikkeli)
            except:
                pass

    def kirjoita_levylle(self,tyyppi,otsikko='',time_stamp='',artikkeli=''):
        kielletyt_merkit = ['<','>',':','"', '/', '\\', '|' ,'?', '*']
        polku = ""
        if tyyppi == 'uutinen':
            polku = self.uutiset + '/'            

            nimi = re.sub(' ','_',otsikko) + r'.txt'            
            for merkki in kielletyt_merkit:                
                if merkki in nimi:                    
                    nimi = nimi.replace(merkki,'')
            nimi = Path(polku + nimi)

            i = 1
            while True:
                print(nimi)  
                if nimi.is_file():
                    nimi = nimi = otsikko + '('+str(i)+')' + r'.txt'
                    nimi = Path(polku + nimi)
                elif not nimi.is_file():
                    with open(str(nimi),'x',encoding="utf-8") as w:
                        w.write(otsikko + '\n')
                        w.write(time_stamp + '\n')
                        w.writelines(artikkeli)

                    break
                i += 1

        elif tyyppi == 'historia':
            polku = self.historia +'/'
        elif tyyppi == 'feature':
            polku = self.featuret + '/'
        elif tyyppi == 'tulos':
            polku = self.tulos + '/'        
        
    def lopeta_driver(self):
        self.driver.quit()


