import praw
import OAuth2Util
import lxml.html as LH


def get_wiki_page(page):
    """Gets content from the wiki

    """
    r = praw.Reddit(user_agent='rolympics using praw')
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="olyconf.ini")
    threads = r.get_subreddit('olympics').get_wiki_page(page).content_md
    return threads

def fetch_medals():
    """Gets the medal count from nbcolympics

    """
    medals_table = "|Rank|Country|Gold|Silver|Bronze|Total|\n|:---|:---|:---|:---|:---|:---|\n"
    tree = LH.parse('http://www.nbcolympics.com/medals')
    rows = [tr for tr in tree.xpath('//*[@id="block-system-main"]/div[2]/div/div[2]/div[3]/div[1]/div/table[1]//tbody/tr')]
    for row in rows:
    	columns = row.getchildren()
    	medals_table += "|" + columns[0].text_content() + "|" + columns[1].text_content().strip() + "|" + columns[2].text_content() + "|" + columns[3].text_content() + "|" + columns[4].text_content() + "|" + columns[5].text_content() + "|\n"
    return medals_table

def set_sidebar_medals():
	""" updates the wiki with current medal count

	"""
	medals_table = fetch_medals()
	r = praw.Reddit(user_agent='rolympics using praw')
	o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="olyconf.ini")
	medals_wiki = r.get_subreddit('olympics').get_wiki_page('sidebar_medals')
	medals_wiki.edit(medals_table)

def update_sidebar():
    """updates the sidebar

    """
    set_sidebar_medals()
    template = get_wiki_page("sidebar_template")
    medals = get_wiki_page("sidebar_medals")
    events = get_wiki_page("sidebar_threads")
    template = template.replace("{{ActiveThreads}}",events)
    template = template.replace("{{Medals}}",medals)
    r = praw.Reddit(user_agent='rolympics using praw')
    o = OAuth2Util.OAuth2Util(r, print_log=True, configfile="olyconf.ini")
    settings = r.get_subreddit("olympics").get_settings()
    settings['description'] = template 
    settings = r.get_subreddit("olympics").update_settings(description=settings['description'])

if __name__ == '__main__':
	update_sidebar()