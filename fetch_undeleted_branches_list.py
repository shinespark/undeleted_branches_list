# coding: utf-8
import csv
import http.cookiejar
import json
import urllib.parse
import urllib.request
import yaml
from bs4 import BeautifulSoup


def main():
    # yaml
    yaml_dict = yaml.load(open('conf.yaml').read())
    ghe_repos_end_point = yaml_dict['github']['end_point']
    repository_name = yaml_dict['github']['repository']

    # login Redmine
    redmine_domain = yaml_dict['redmine']['end_point']
    redmine_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    redmine_post = {
        'username': yaml_dict['redmine']['username'],
        'password': yaml_dict['redmine']['password']
    }
    redmine_query = urllib.parse.urlencode(redmine_post).encode('utf-8')
    redmine_opener.open(redmine_domain + '/login', redmine_query)

    # fetch branches list
    default_param = '?access_token=' + yaml_dict['github']['access_token']
    api_name = '/branches'
    all_branch_list = fetch_all(ghe_repos_end_point + repository_name + '/branches' + default_param)

    #  fetch branch_name, author, redmine_url per branch
    results = []
    for branch in all_branch_list:
        branch_name = branch['name']
        print(branch_name)

        # fetch branch
        api_name = '/branches/' + branch_name
        branch_dict = json.loads(urllib.request.urlopen(ghe_repos_end_point + repository_name + api_name + default_param).read().decode('utf-8'))

        author = branch_dict['commit']['commit']['author']['name']
        url = branch_dict['_links']['html']

        # fetch redmine's ticket url
        redmine_issue_title = redmine_issue_status = redmine_issue_url = ''
        if branch_name.startswith('id/'):

            redmine_issue_url = redmine_domain + '/issues/' + branch_name.lstrip('id/')
            soup = BeautifulSoup(redmine_opener.open(redmine_issue_url).read().decode('utf-8'), 'html.parser')
            redmine_issue_title = soup.title.string.split(' - ')[0]
            td_status = soup.find('td', class_='status')
            if td_status:
                redmine_issue_status = td_status.string

        results.append([
            branch_name,
            author,
            url,
            redmine_issue_title,
            redmine_issue_status,
            redmine_issue_url
        ])

    # order by author, branch_name
    results.sort(key=lambda x: x[0])
    results.sort(key=lambda x: x[1])

    # write csv
    csv_header = [
        'branch_name',
        'author',
        'url',
        'redmine_issue_title',
        'redmine_issue_status',
        'redmine_issue_url'
    ]
    csv_file = open('undeleted_branch_list.csv', 'w')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(csv_header)

    for result in results:
        csv_writer.writerow(result)

    print('取得完了!')


def fetch_all(url, all_list=None):
    # init
    if all_list is None:
        all_list = []

    res = urllib.request.urlopen(url)
    res_link, res_body = res.getheader('Link'), res.read().decode('utf-8')
    all_list += json.loads(res_body)

    if 'rel="next"' in res_link:
        next_url = res_link.split('; rel="next"')[0].strip('<>')
        fetch_all(next_url, all_list)

    return all_list

if __name__ == "__main__":
    main()
