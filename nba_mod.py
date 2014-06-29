class NBAModBot(object):
    #def __init__(self):
    #    self.username = getpass("Username: ")
    #    self.password = getpass()
        
    def get_username(self):
        return self.username
        
    def get_password(self):
        return self.password

    
    def create_sidebar(self):
        """Get the static sidebar elements and callouts to dynamic sidebar
        elements from the /r/NBA wiki. 

        Last revised 09/15/2013
        
        """
        #Initiate PRAW
        r = praw.Reddit(user_agent='NBA_MOD using praw')
        #Log in to Reddit using 
        r.login(self.username,self.password)
        #Get the sidebar from the wiki
        sidebar_md = r.get_subreddit('NBA').get_wiki_page('edit_sidebar').content_md
        #Split the sidebar by individual lines. Each line is a different game
        sidebar_list = sidebar_md.split('\n')
        sidebar = ""
        for line in sidebar_list:
            if line.startswith("//")==False: 
                if line.startswith("$kill"):
                    return "kill"
                elif line.startswith("$team_subreddits"):
                    #Need to incorporate arguments!
                    sidebar = sidebar + self.get_team_subreddits(5)
                elif line.startswith("$schedule"):
                    #Need to incorporate arguments!
                    sidebar = sidebar + self.get_schedule(4)
                elif line.startswith("$game_threads"):
                    sidebar = sidebar + self.get_game_threads()
                elif line.startswith("$standings"):
                    sidebar = sidebar + self.get_standings()
                else:
                    sidebar = sidebar + line

        return sidebar
    
    def update_sidebar(self,var_sidebar):
        """Updates /r/NBA. 

        Last revised 09/15/2013
        
        """
        #Initiate PRAW
        r = praw.Reddit(user_agent='NBA_MOD using praw')
        #Log in to Reddit using 
        r.login(self.username,self.password)
        settings = r.get_subreddit('NBA').get_settings()
        settings['description'] = var_sidebar 
        settings = r.get_subreddit('NBA').update_settings(description=settings['description'])
            
    