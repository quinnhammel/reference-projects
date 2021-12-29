import praw
import time
id = '*****'
secret = '*****'
username = 'AssholeTallierBot'
password = '*****'
user_agent = 'Asshole_Tallier'
def getSubComments(comment, allComments, verbose=True):
    allComments.append(comment)
    if not hasattr(comment, "replies"):
        replies = comment.comments()
        if verbose: 
            print("fetching (" + str(len(allComments)) + " comments fetched total)")
    else:
        replies = comment.replies
    for child in replies:
        getSubComments(child, allComments, verbose=verbose)

def getAll(r, submissionId, verbose=True):
    submission = r.submission(submissionId)
    comments = submission.comments
    commentsList = []
    for comment in comments:
        getSubComments(comment, commentsList, verbose=verbose)
    return commentsList

if __name__ == "__main__":
    reddit = praw.Reddit(client_id=id, client_secret=secret, username=username, password=password, user_agent=user_agent)
    subreddit = reddit.subreddit('AmItheAsshole')
    hot_asshole = subreddit.hot(limit=3)

    index= 0

    t = time.time()
    '''
    for submission in hot_asshole:
        notasshole = 0
        asshole = 0
        total = 0
        try:
            if not submission.stickied:
                print(submission.id)
                submission.comments.replace_more()
                comments = submission.comments
                for comment in comments:
                    if not comment.stickied:
                        body = comment.body
                        body = ' '.join(body.split()).upper()
                        #check first 10 characters for the rating
                        ratingbody = body[0:10]
                        if 'NTA' in ratingbody:
                            #should also not have yta in it
                            if not 'YTA' in ratingbody:
                                notasshole += 1
                        elif 'YTA' in ratingbody:
                            asshole += 1
                        total += 1
                t = time.time() - t
                print('For post \"{}\", out of {} total comments, {} voted NTA and {} voted YTA.'.format(submission.title,
                total, notasshole, asshole))
                print('So, {} cast a valid vote. And of those, {} voted NTA.'.format((notasshole+asshole)/total,
                notasshole/(asshole+notasshole)))
                print('Replace_more search took {}s'.format(t))
        except:
            pass
            '''
    reddit = praw.Reddit(client_id=id, client_secret=secret, username=username, password=password, user_agent=user_agent)
    subreddit = reddit.subreddit('AmItheAsshole')
    hot_asshole = subreddit.hot(limit=3)
    t = time.time()
    for submission in hot_asshole:
        notasshole = 0
        asshole = 0
        total = 0
        try:
            if not submission.stickied:
                comments = submission.comments
                for comment in comments:
                    try:
                        if not comment.stickied:
                            print(comment.ups)
                            body = comment.body
                            body = ' '.join(body.split()).upper()
                            #check first 10 characters for the rating
                            ratingbody = body[0:10]
                            if 'NTA' in ratingbody:
                                #should also not have yta in it
                                if not 'YTA' in ratingbody:
                                    notasshole += 1
                            elif 'YTA' in ratingbody:
                                asshole += 1
                            total += 1
                    except:
                        pass
                    
                t = time.time() - t
                print('For post \"{}\", out of {} total comments, {} voted NTA and {} voted YTA.'.format(submission.title,
                total, notasshole, asshole))
                print('So, {} cast a valid vote. And of those, {} voted NTA.'.format((notasshole+asshole)/total,
                notasshole/(asshole+notasshole)))
                print('Default search took {}s'.format(t))
        except:
            pass

    notasshole = 0
    asshole = 0
    total = 0
    t = time.time()

    comments = getAll(reddit, 'c1dpdc', verbose=False)

    for comment in comments:
        try:
            if not comment.stickied:
                body = comment.body
                body = ' '.join(body.split()).upper()
                #check first 10 characters for the rating
                ratingbody = body[0:10]
                if 'NTA' in ratingbody:
                    #should also not have yta in it
                    if not 'YTA' in ratingbody:
                        notasshole += 1
                elif 'YTA' in ratingbody:
                    asshole += 1
                total += 1
        except:
            pass
    t = time.time() - t    
    print('Out of {} total comments, {} voted NTA and {} voted YTA.'.format(total, notasshole, asshole))
    print('So, {} cast a valid vote. And of those, {} voted NTA.'.format((notasshole+asshole)/total,
    notasshole/(asshole+notasshole)))
    print('Special search took {}s'.format(t))




