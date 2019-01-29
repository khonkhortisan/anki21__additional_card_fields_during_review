######################################
######################################
###mod for Dedu6ka

            ############## USER CONFIGURATION START ##############

            OVERDUE_THRESHOLD = 0.1
            VERY_MATURE_THRESHOLD_IN_DAYS = 180 

            BG_COLOR_VERYMATURE = "#beffb2"
            BG_COLOR_VERYMATURE_AND_OVERDUE = "#ffe96a"
            BG_COLOR_OVERDUE = "#ff988a"

            OVERDUE_WARNING_TEXT = '<b><font size="25"><font color="red">This card is overdue for more than 10%</font></b></font>'

            OVERDUE_TOOLTIP = False

            MMM = 40   
            MMM_BG_COLOR = "#a5ffec"   #might conflict with other bg-colors-options

            ##############  USER CONFIGURATION END  ##############


            #inspired by cPrevIvl from advanced browser by HSSM
            #https://github.com/hssm/advanced-browser/blob/master/advancedbrowser/advancedbrowser/custom_fields.py#L161
            def Prior_Ivl(card, mymwcol, n, ivl=0):
                if n != 0:
                    ivl = eval('mymwcol.db.scalar("select ivl from revlog where cid = ? order by id desc limit ' +  str(n) + ' offset ' + str(n) + ' ", card.id)  ')
                
                one, two = "",""
                
                if ivl is None:
                    one = ""
                elif ivl == 0:
                    one  = 0
                    two  = "0 days"
                elif ivl > 0:
                    one = ivl
                    two = fmtTimeSpan(ivl*86400)
                else:
                    one = ""
                    two = timefn(-ivl)
                return one, two


            #modification of function  _revlogData from Addon Extended Card Stats
            #which is 
            #   Copyright: (c) Glutanimate 2016-2017 <https://glutanimate.com/>
            def correct_streak(card, d, f='days'):
                """ return number of steps_and_reviews, reviews and days since last fail/again"""
                entries = d.db.all(
                    "select id/1000.0, ease, ivl, factor, time/1000.0, type "
                    "from revlog where cid = ?", card.id)
                if not entries:
                    return ""

                latest_total_fail_index = 0
                latest_total_fail_date = int(card.id/1000)    #initializing with creation time

                latest_review_fail_index = 0
                latest_review_fail_date = int(card.id/1000)    #initializing with creation time
                
                for index, (date, ease, ivl, factor, taken, type) in enumerate(entries):
                    if ease == 1:
                        latest_total_fail_date = date
                        latest_total_fail_index = index

                
                out = []

                total_number_of_revs = len(entries)
                if latest_total_fail_index == 0:
                    out.append(total_number_of_revs - latest_total_fail_index) 
                else:
                    out.append(total_number_of_revs - latest_total_fail_index - 1)        

                
                num_succesful_reviews=0
                for index, (date, ease, ivl, factor, taken, type) in enumerate(reversed(entries)):
                    if type == 1:
                        num_succesful_reviews += 1
                    else:
                        break
                out.append(num_succesful_reviews)

                now = int(time.time())
                diff = now - latest_total_fail_date

                if f == 'sec':
                    out.append(diff)
                if f == 'days':
                    out.append(int(diff/24/60/60))

                return out


            def adjust_background_for_card_properties(overdue=False, very_mature=False):
                if overdue == True and very_mature == True:
                    return '<style>.card { background-color: ' + BG_COLOR_VERYMATURE_AND_OVERDUE + ' ! important; }</style>'
                elif overdue == True:
                    return '<style>.card { background-color: ' + BG_COLOR_OVERDUE + ' ! important; }</style>'
                elif very_mature == True:
                    return '<style>.card { background-color: ' + BG_COLOR_VERYMATURE + ' ! important; }</style>'
                else:
                    return ""
  

            p0ivl_d, p0ivl_f = Prior_Ivl(card, d, 0, card.ivl)
            addInfo['Ivl_days'] = card.ivl  # or p0ivl_d
            if p0ivl_d:
                addInfo['Ivl_fmt'] = p0ivl_f


            p1ivl_d, p1ivl_f = Prior_Ivl(card, d, 1)  # Previous_Ivl
            if p1ivl_d:
                addInfo['Previous_Ivl_days'] = p1ivl_d
                addInfo['Previous_Ivl_fmt'] = p1ivl_f

            p2ivl_d, p2ivl_f = Prior_Ivl(card, d, 2) # Penultimate Ivl
            if p2ivl_d:
                addInfo['Penultimate_Ivl_days'] = p2ivl_d
                addInfo['Penultimate_Ivl_fmt'] = p2ivl_f

            p3ivl_d, p3ivl_f = Prior_Ivl(card, d, 3)
            if p3ivl_d:
                addInfo['p3vl_days'] = p3ivl_d
                addInfo['p3vl_fmt'] = p3ivl_f
    
            try:
                myivls = [int(x) for x in [p0ivl_d,p1ivl_d,p2ivl_d]]
            except:
                pass
            else:
                if all(i >= MMM for i in myivls):
                    addInfo['three_reps_larger_than_MMM_value'] = 1
                    addInfo['three_reps_larger_than_MMM_color'] = '<style>.card { background-color: ' + MMM_BG_COLOR  + ' ! important; }</style>' 


            corst =  correct_streak(card, d)
            if corst:
                addInfo['correct_streak__num_of_steps_and_reviews'] = corst[0]
                addInfo['correct_streak__num_of_reviews'] = corst[1]
                addInfo['correct_streak__days_since_fail'] = corst[2]

            if card.ivl >= VERY_MATURE_THRESHOLD_IN_DAYS:
                addInfo['change_background_verymature_and_overdue'] = adjust_background_for_card_properties(overdue=True, very_mature=True)


            if cOverdueIvl:      
                scheduled_ivl_before_todays_review_in_days = card.ivl
                overdue_in_days = cOverdueIvl 
                if overdue_in_days / scheduled_ivl_before_todays_review_in_days  > OVERDUE_THRESHOLD:
                    addInfo['overdue_warning_message'] = OVERDUE_WARNING_TEXT
                    addInfo['change_background_only_overdue'] = adjust_background_for_card_properties(overdue=True, very_mature=False)
                    addInfo['change_background_verymature_and_overdue'] = adjust_background_for_card_properties(overdue=True, very_mature=True)
                    addInfo['overdue_warning_value'] = 1 # might be useful for conditional formatting? 
                    if OVERDUE_TOOLTIP:
                        tooltip('The card is more overdue than ' + str(int(OVERDUE_THRESHOLD * 100)) + '%')  # message, time in milliseconds



###end mod
######################################
######################################
