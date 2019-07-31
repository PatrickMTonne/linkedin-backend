import pandas
from numpy import savetxt

df = pandas.read_csv('/Users/patricktonne/Downloads/query_result.csv')
savetxt(r'/Users/patricktonne/desktop/urls.txt', df['url'], fmt='%s')
