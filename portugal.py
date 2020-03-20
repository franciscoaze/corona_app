from PyPDF4 import PdfFileReader
import pandas as pd
from pathlib import Path
import requests
from matplotlib import pyplot as plt
from bs4 import BeautifulSoup
import openpyxl
import tika
from tika import parser


class PDFscrapper:

    def __init__(self):
        self.report_nr = 0

    def get_file(self,nr):
        # Retrieve html text from url
        try:
            url = 'https://covid19.min-saude.pt/relatorio-de-situacao/'
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find(id='content_easy')
            links = results.find_all('li')
            line = links[0].find('a')

            # Check if last link is the correct one
            current_pdf = int(line.contents[0].split('º')[1].split('|')[0])
            if current_pdf == nr:
                # This is the one pretended
                pdf_url = line['href']
                print(f"Downloading {line.contents[0]}")

                resp = requests.get(pdf_url)
                pathname = f"reports/rel{nr}.pdf"
                filename = Path(pathname)
                filename.write_bytes(resp.content)

                return True

            else:
                print('Already have this one.')
                return False
        except:
            print('Couldnt read page')
            return False


class Report:

    def __init__(self):
        self.text = []
        self.date_until = []
        self.updated_at = []
        self.cases = []

    def text_extractorOLD(self,path):
        with open(path, 'rb') as f:
            pdf = PdfFileReader(f)
            # get the first page
            page = pdf.getPage(1)
            # print(page)
            # print('Page type: {}'.format(str(type(page))))
            self.text = page.extractText().split('\n')
            # print(text)
            return self.text

    def text_extractor(self,path):
        parsed = parser.from_file(path)
        self.text = parsed['content'].split('\n')
        return self.text

    def text_interpreter(self):
        text = self.text
        # Até dia
        idx = text.index('Saiba mais em https://covid19.min-saude.pt/')
        piece = text[idx-3].split()
        if piece == []:
            piece = text[idx - 4].split()
        self.date_until = [piece[3],piece[5],piece[9]]
        piece = text[idx - 2].split()
        self.updated_at = [piece[2], piece[4], piece[8]]
        # Casos confirmados
        # Continuam a mudar o formato quase todos os dias... Agora com percentagens 19/03
        casos = []
        idx = text.index('GRUPO ETÁRIO MASCULINO FEMININO')
        casos.append(['0-9', int(text[idx+2].split()[2]), int(text[idx+2].split()[3])])
        casos.append(['10-19', int(text[idx + 4].split()[2]), int(text[idx + 4].split()[3])])
        casos.append(['20-29', int(text[idx + 6].split()[2]), int(text[idx + 6].split()[3])])
        casos.append(['30-39', int(text[idx + 8].split()[2]), int(text[idx + 8].split()[3])])
        casos.append(['40-49', int(text[idx + 10].split()[2]), int(text[idx + 10].split()[3])])
        casos.append(['50-59', int(text[idx + 12].split()[2]), int(text[idx + 12].split()[3])])
        casos.append(['60-69', int(text[idx + 14].split()[2]), int(text[idx + 14].split()[3])])
        casos.append(['70-79', int(text[idx + 16].split()[2]), int(text[idx + 16].split()[3])])
        casos.append(['80+', int(text[idx + 18].split()[1]), int(text[idx + 18].split()[2])])

        self.cases = pd.DataFrame(casos, columns=['Idades', 'M', 'F'])


    def text_interpreterOLD(self):
        # Até dia [dia,mes,hora]
        text = self.text
        idx = text.index('até dia')
        self.date_until.append(int(text[idx+1].split()[0]))
        piece = text[idx+2].split()[1]
        if piece == '|':
            piece = text[idx + 2].split()[0]
        self.date_until.append(piece)
        self.date_until.append( int(text[idx + 3].split(':')[0]))

        # Actualizado a [dia,mes,hora]
        idx = text.index('Atualizado a ')
        self.updated_at.append(int(text[idx+1].split()[0]))
        self.updated_at.append(text[idx+2].split()[1])
        self.updated_at.append(int(text[idx + 3].split(':')[0]))

        # Casos Confirmados
        idx = text.index('CARACTERIZAÇÃO DOS')
        casos = []
        casos.append(['0-9',int(text[idx+13]),int(text[idx+14])])
        idx+=14
        casos.append(['10-19',int(text[idx + 5]), int(text[idx + 6])])
        idx+=11
        casos.append(['20-29',int(text[idx]), int(text[idx + 1])])
        idx+=6
        casos.append(['30-39',int(text[idx]), int(text[idx + 1])])
        idx += 6
        casos.append(['40-49',int(text[idx]), int(text[idx + 1])])
        idx += 6
        casos.append(['50-59',int(text[idx]), int(text[idx + 1])])
        idx += 6
        casos.append(['60-69',int(text[idx]), int(text[idx + 1])])
        idx += 6
        casos.append(['70-79',int(text[idx]), int(text[idx + 1])])
        idx += 3
        casos.append(['80+',int(text[idx]), int(text[idx + 1])])

        self.cases = pd.DataFrame(casos,columns = ['Idades','M','F'])

    def save2excel(self,nr):
        # TODO if sheet already exist, overwrite it
        with pd.ExcelWriter('reports/corona.xlsx', mode='a', engine="openpyxl") as writer:
            self.cases.to_excel(writer, sheet_name=f"r{nr}")

class Manager:

    def __init__(self):
        # Check what is the next number to check
        f = open("vars.txt", "r")
        line = f.readline()
        f.close()
        self.prev_nr = int(line[9:])
        self.nr = self.prev_nr+1
        self.last = []
        self.df = pd.DataFrame()

        pd.options.plotting.backend = 'matplotlib'
        plt.style.use('seaborn')

        self.p = PDFscrapper()
        self.r = Report()

        self.get_last()
        self.dates = []

    def get_reportPDF(self,nr):
        self.r = Report()
        pathname = f"reports/rel{nr}.pdf"
        self.r.text_extractor(pathname)
        self.r.text_interpreter()
        date = self.r.date_until
        return self.r.cases, date

    def get_allCSV(self):
        """IN USE"""
        df = pd.read_csv('reports/corona.txt')
        df.set_index(['Report', 'Idades'], inplace=True)
        df.sort_index(inplace=True)
        self.df = df
        self.dates = df['Date'].unique().tolist()
        return self.df

    def save2csv(self):
        """IN USE"""
        self.df.to_csv('reports/corona.txt')

    def get_new(self):
        new = self.p.get_file(self.nr)
        if new:
            [new_df,date] = self.get_reportPDF(self.nr)

            self.r.save2excel(self.nr)
            self.last = self.r.cases
            date_str = f"{date[0]}{date[1]}"
            self.dates.append(date_str)

            new_df.insert(3,'Total',new_df['M'].add(new_df['F']))
            new_df.insert(4, 'Report', self.nr)
            new_df.insert(5, 'Date', date_str)

            new_df.set_index(['Report', 'Idades'], inplace=True)
            # Add new cases dataframe to main df if it exists
            if not self.df.empty:
                self.df = pd.concat([self.df,new_df])
                self.df.sort_index(inplace=True)
                print('Added values to main df.')
            print('Saving to excel and updating vars.txt')

            f = open("vars.txt","w")
            f.write(f"last_nr = {self.nr}")
            f.close()
            self.prev_nr=self.nr
            self.nr +=1
        else:
            print('No new reports.')

    def plot(self,type):
        if type == 'last':
            self.get_last()
            ax = self.last.plot.bar(y = ['M','F'], stacked=True,rot=45,grid=True)
            for i,total in zip(ax.patches[0:9],self.last['Total']):
                s =f"{total}".rjust(3)
                ax.text(i.get_x()+0.07, total + .8, \
                        s, fontsize=10,
                        color='black')

        elif type == 'ages':
            if not self.df.empty:
                plt.figure()
                self.df.groupby('Idades')['Total'].plot(ax=plt.gca(), legend=True)
                date_ticks = [f"{d[:5]}" for d in self.dates]
                plt.xticks(range(len(date_ticks)), date_ticks)
                plt.xlabel('Data')
                # TODO trocar aqui
                ages = self.df.index.get_level_values(1).unique()
                for lab in ages:
                    kwargs = {'textcoords':"offset points","xytext":(5,0),'ha':'left'}
                    # last_val = self.df.loc[lab]['Total'].tail(1)
                    last_val = m.df.loc[self.prev_nr,'Total'][lab]
                    plt.annotate(lab,(len(date_ticks)-1,last_val),**kwargs)

    def print_info(self):
        reports = self.df.index.get_level_values(0).unique().to_list()
        print("Available Reports-----------------")
        for rep,dat in zip(reports,self.dates):
            # date = " ".join(dat)
            print(f"Report {rep} | {dat}")
        last_total = self.df.loc[self.prev_nr-1]['Total'].sum()
        curr_total = self.get_last()['Total'].sum()
        diff = curr_total - last_total
        print(f"Total number of cases: {curr_total} (+{diff})")

    def get_last(self):
        """RARE USE
        Usado para testes e facil acesso
        """
        self.last = pd.read_excel('reports/corona.xlsx',usecols = ['Idades','M','F'],sheet_name=f'r{self.prev_nr}',index_col = 'Idades')
        self.last.insert(2, 'Total', self.last['M'].add(self.last['F']))
        return self.last

    def get_allPDFs(self):
        """OLD
        Ia ler todos os pdfs para retirar as informações. Substituido por get_allCSV()
        """
        start=10
        dfs=[]

        for f in range(start,self.prev_nr+1):
            [new,date] = self.get_reportPDF(f)
            new.insert(3,'Total',new['M'].add(new['F']))
            new.insert(4, 'Report', f)
            date_str = f"{date[0]}{date[1]}"
            new.insert(5,'Date',date_str)
            dfs.append(new)
            self.dates.append(date_str)
        self.df = pd.concat(dfs)
        self.df.set_index(['Report', 'Idades'], inplace=True)
        self.df.sort_index(inplace=True)


if __name__ == '__main__':
    # TODO por valores em cima das barras
    # TODO graficos sintomas
    # TODO slider temporal
    # TODO Fazer limpeza ao codigo
    # TODO subplots

    m = Manager()
    m.get_allCSV()
    m.get_new()
    m.save2csv()
    m.print_info()
    m.plot('ages')
    m.plot('last')
    plt.show()


