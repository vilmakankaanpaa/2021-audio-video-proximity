
# TODO: can I just collectively leave the second baseline out of the data instead of filtering it here and there?

library(tidyverse)
library(gridExtra)

# Set directory to where this file resides.
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Load data
df <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, date, study_day, test_phase, test_phase_day, using_stimuli, condition, stimulus, switch, content, starttime, duration, individual)
df

# What are the data types of columns?
str(df)

# Change some data types
df$period_id <- as.character(df$period_id)
df$ix_id <- as.character(df$ix_id)
df$switch <- as.factor(df$switch)
df$starttime <- as.character(df$starttime)
df$test_phase_day <- as.factor(df$test_phase_day)

# Data now
head(df)


# BASIC VALUES
monkeys = 3
study_days = 32
labels <- c(
  "1-control-prior" = "1. No-stimuli",
  "2-audio-1"= "2. Audio 1", 
  "3-visual-1" = "3. Visual 1", 
  "4-audio-2" = "4. Audio 2", 
  "5-visual-2" = "5. Visual 2",
  "6-audio-3" = "6. Audio 3",
  "7-visual-3" = "7. Visual 3",
  "8-control-post" = "8. No-stimuli")


# ------------------------------------------------ TRANSFORM DATA ------------------------------------------------------------------------

# DATA BASED ON STUDY DAY

# Collect summary data for each study day
data.daily <- df %>% group_by(stimulus, using_stimuli, condition, test_phase, test_phase_day, study_day) %>% 
  summarise(
    periods = n_distinct(period_id),
    periods.monkey = n_distinct(period_id)/monkeys,
    interactions = n_distinct(ix_id),
    interactions.monkey = n_distinct(ix_id)/monkeys,
    usetime = sum(duration),
    usetime.monkey = sum(duration)/monkeys
  )

# IF GOING TO TAKE ANY MEANS, NEED TO ADD EMPTY ROWS FOR MISSING DAYS

# video 2
data.daily <- bind_rows(data.daily, list(stimulus='visual', using_stimuli=TRUE, condition='stimuli', test_phase='5-visual-2', test_phase_day="3", study_day=19, periods=0, periods.monkey=0, interactions=0, interactions.monkey=0, usetime=0, usetime.monkey=0))

# audio 3
data.daily <- bind_rows(data.daily, list(stimulus='auditory', using_stimuli=TRUE, condition='stimuli', test_phase='6-audio-3', test_phase_day="3", study_day=22, periods=0, periods.monkey=0, interactions=0, interactions.monkey=0, usetime=0, usetime.monkey=0))

# Posterior baseline
data.daily <- bind_rows(data.daily, list(stimulus='no-stimulus', using_stimuli=FALSE, condition='second-baseline', test_phase='8-control-post', test_phase_day="2", study_day=27, periods=0, periods.monkey=0, interactions=0, interactions.monkey=0, usetime=0, usetime.monkey=0))


# Arrange the table
data.daily <- data.daily %>% arrange(study_day)

data.daily

# DATA BASED ON INTERACTIVITY PERIODS (combine interactions together)

# Group the data by the interactive periods. 
#   Calculate the duration of period by sum of its interaction durations. 
#   Pick the starttime as the earliest time of its interactions.
df.periods <- df %>% group_by(period_id, date, study_day, test_phase, test_phase_day, stimulus, switch, content, individual, using_stimuli, condition) %>%
  summarise(
    stimulus_interactions = n_distinct(ix_id),
    starttime = min(starttime),
    duration = sum(duration)
  )

df.periods


# ------------------------------------------------ ANALYSIS ------------------------------------------------------------------------


# 1 Sumary stats -------------------------------------------------------------------------------------------------------------------

# Interactive periods: total, daily, per monkey, daily per monkey
# Button interactions: total, daily, per monkey, daily per monkey
# Interaction time: total, per monkey, daily per monkey, SD

# A - WHOLE STUDY

tab1 <- df %>% summarise(
  'Interactive periods' = n_distinct(period_id),
  'Button interactions' = n_distinct(ix_id),
  'AVG. daily interactive periods' = n_distinct(period_id)/study_days,
  'AVG. daily button interactions' = format(round(n_distinct(ix_id)/study_days,2),nsmall=2),
  'AVG. daily interaction time' = format(round(sum(duration)/study_days,2),nsmall=2)
)

tab1

png("1-A summary_whole-study.png",height=150,width=800)
grid.table(tab1)
dev.off()

# B - NO-STIMULI VS STIMULI

tab2 <- data.daily %>% filter(condition!='second-baseline') %>% group_by(condition) %>% 
  summarise(
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Mean interactive periods daily per monkey' = format(round(mean(periods.monkey),2),nsmall=2),
    'Button Interactions' = sum(interactions),
    'Mean button Interactions daily per monkey' = format(round(mean(interactions.monkey),2),nsmall=2),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    'Mean interaction time (s) daily per monkey' = format(round(mean(usetime.monkey),2),nsmall=2),
    'SD of interaction time (s) daily per monkey' = format(round(sd(usetime.monkey),2),nsmall=2)
  )

tab2

png("1-B summary_using-stimuli.png",height=150,width=1600)
grid.table(tab2)
dev.off()

# C - STIMULI TYPE (AUDIO, VISUAL, NO)

tab3 <- data.daily %>% filter(condition!='second-baseline') %>% group_by(stimulus) %>% 
  summarise(
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Interactive periods daily per monkey' = format(round(mean(periods.monkey),2),nsmall=2),
    'Button Interactions' = sum(interactions),
    'Button Interactions daily per monkey' = format(round(mean(interactions.monkey),2),nsmall=2),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    'Interaction time (s) daily per monkey' = format(round(mean(usetime.monkey),2),nsmall=2),
    'SD of interaction time (s) daily per monkey' = format(round(sd(usetime.monkey),2),nsmall=2)
  )

tab3

png("1-C summary_stimuli-type.png",height=150,width=1600)
grid.table(tab3)
dev.off()

# D - CYCLES

tab4 <- data.daily %>% group_by(test_phase) %>% 
  summarise(
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Interactive periods daily per monkey' = format(round(mean(periods.monkey),2),nsmall=2),
    'Button Interactions' = sum(interactions),
    'Button Interactions daily per monkey' = format(round(mean(interactions.monkey),2),nsmall=2),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    'Interaction time (s) daily per monkey' = format(round(mean(usetime.monkey),2),nsmall=2),
    'SD of interaction time (s) daily per monkey' = format(round(sd(usetime.monkey),2),nsmall=2)
  )

tab4

png("1-D summary_cycles.png",height=150,width=1600)
grid.table(tab4)
dev.off()


# 2 Duration of interactivity periods ----------------------------------------------------------------------------------------

# Interactions = Interactivity periods
# Collect the stats about interactive period durations: 
#   Mean, median, std, longest, shortest

# A - WHOLE STUDY

results.periods <- df.periods %>% group_by() %>% summarise(
  'Mean duration' = format(round(mean(duration),2), nsmall=2),
  'Median duration' = format(round(median(duration),2), nsmall=2),
  'SD of duration' = format(round(sd(duration),2), nsmall=2),
  'Longest duration' = format(round(max(duration),2),nsmall=2),
  'Shortest duration' = format(round(min(duration),2), nsmall=2)
)

results.periods

png("2-A duration_whole-study.png",height=150,width=800)
grid.table(results.periods)
dev.off()


# B - NO STIMULI VS STIMULI

results.periods <- left_join(data.daily %>% filter(condition!='second-baseline') %>% group_by(condition) %>%
                               summarise(
                                 'Interactive periods' = sum(periods)
                               ), 
                             df.periods %>% filter(condition!='second-baseline') %>% group_by(condition) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.periods

# Print out the results table. Saved to the same directory as the file is at.
png("2-B duration_using-stimuli.png",height=150,width=800)
grid.table(results.periods)
dev.off()

# C - STIMULI TYPE

results.periods <- left_join(data.daily %>% filter(condition!='second-baseline') %>% group_by(stimulus) %>%
                               summarise(
                                 'Interactive periods' = sum(periods)
                               ), 
                             df.periods %>% filter(condition!='second-baseline') %>% group_by(stimulus) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.periods

# Print out the results table. Saved to the same directory as the file is at.
png("2-C duration_stimuli-type.png",height=150,width=800)
grid.table(results.periods)
dev.off()

# D - CYCLES

results.periods <- left_join(data.daily %>% group_by(test_phase) %>%
                               summarise(
                                 'Interactive periods' = sum(periods)
                               ), 
                             df.periods %>% group_by(test_phase) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.periods

# Print out the results table. Saved to the same directory as the file is at.
png("2-D duration_cycles.png",height=150,width=800)
grid.table(results.periods)
dev.off()



# 3 Duration of button interactions ----------------------------------------------------------------------------------------

# Interactions = Button interactions

# A - WHOLE STUDY

results.buttons <- df %>% group_by() %>% summarise(
  'Mean duration' = format(round(mean(duration),2), nsmall=2),
  'Median duration' = format(round(median(duration),2), nsmall=2),
  'SD of duration' = format(round(sd(duration),2), nsmall=2),
  'Longest duration' = format(round(max(duration),2),nsmall=2),
  'Shortest duration' = format(round(min(duration),2), nsmall=2)
)

results.buttons

png("3-A duration_whole-study.png",height=150,width=800)
grid.table(results.buttons)
dev.off()

# B - USING STIMULI
results.buttons <- left_join(data.daily %>% filter(condition!='second-baseline') %>% group_by(condition) %>%
                               summarise(
                                 'Button interactions' = sum(interactions)
                               ), 
                             df %>% filter(condition!='second-baseline') %>% group_by(condition) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.buttons

png("3-B duration_using-stimuli.png",height=150,width=800)
grid.table(results.buttons)
dev.off()

# C - STIMULI TYPE

results.buttons <- left_join(data.daily %>% filter(condition!='second-baseline') %>% group_by(stimulus) %>%
                               summarise(
                                 'Button interactions' = sum(interactions)
                               ), 
                             df %>% filter(condition!='second-baseline') %>% group_by(stimulus) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.buttons

png("3-C duration_stimuli-type.png",height=150,width=800)
grid.table(results.buttons)
dev.off()

# D - CYCLES

results.buttons <- left_join(data.daily %>% group_by(test_phase) %>%
                               summarise(
                                 'Button interactions' = sum(interactions)
                               ), 
                             df %>% group_by(test_phase) %>% 
                               summarise(
                                 'Mean duration' = format(round(mean(duration),2), nsmall=2),
                                 'Median duration' = format(round(median(duration),2), nsmall=2),
                                 'SD of duration' = format(round(sd(duration),2), nsmall=2),
                                 'Longest duration' = format(round(max(duration),2),nsmall=2),
                                 'Shortest duration' = format(round(min(duration),2), nsmall=2)
                               )
)

results.buttons

png("3-D duration_cycles.png",height=150,width=800)
grid.table(results.buttons)
dev.off()




# 4 TRAJECTORY OF DAILY USAGE ----------------------------------------------------------------------------------------

# Interaction time per monkey
g1 <- ggplot(data=data.daily, aes(study_day, usetime.monkey)) + #fill=test_phase
  #geom_line() +
  #geom_point() +
  geom_col() +
  geom_smooth(se=FALSE) +
  scale_x_continuous(breaks=seq(1,32,1)) +
  scale_y_continuous(breaks=seq(0,24,2)) +
  xlab('Study day') +
  ylab('Interaction time per monkey (s)') +
  #labs(title='Interaction time per monkey') +
  theme_minimal()

g1 <- g1 + theme(panel.grid.minor = element_blank())

g1

ggsave("4-periods-trajectory-cols-n-smooth.png", g1, width=8.5, height=4.5)  

# By cycles

g2 <- ggplot(data=data.daily, aes(test_phase, usetime.monkey)) +
  geom_col() +
  scale_y_continuous(breaks=seq(0,70,5)) +
  xlab(NULL) +
  ylab('Interaction time per monkey (s)') +
  scale_x_discrete(labels = labels) +
  #labs(title='Interaction time per monkey') +
  theme_minimal()

g2 <- g2 + theme(panel.grid.minor = element_blank())

g2

ggsave("4-2_cycle-trajectory.png", g2, width=6.5, height=4.5)  


png("4-B table-cycles-usage.png",height=200,width=300)
grid.table(
  data.daily %>% group_by(test_phase) %>%
    summarise('interaction time (s)' =round(sum(usetime.monkey),1))
)
dev.off()



# 5 INDIVIDUAL USAGE -----------------------------------------------------------------------------------------------

# WHOLE STDUY
individuals <- df.periods %>% group_by(individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(stimulus_interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  )
individuals

png("5-A individuals_whole-study.png",height=150,width=800)
grid.table(individuals)
dev.off()

# NO STIMULI V STIMULI

individuals <- df.periods %>% filter(condition!='second-baseline') %>% group_by(condition, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(stimulus_interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  )
individuals

png("5-B individuals_using-stimuli.png",height=150,width=800)
grid.table(individuals)
dev.off()

# STIMULI TYPE

individuals <- df.periods %>% filter(condition!='second-baseline') %>% group_by(stimulus, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(stimulus_interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  )
individuals

png("5-C individuals_stimuli-type.png",height=150,width=800)
grid.table(individuals)
dev.off()

# CYCLES

individuals <- df.periods %>% group_by(test_phase, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(stimulus_interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  )
individuals

png("5-D individuals-cycles.png",height=500,width=800)
grid.table(individuals)
dev.off()


# 6 BUTTON USAGE -----------------------------------------------------------------------------------------------

png("6-Button usage.png",height=150,width=300)
grid.table(
  df %>% group_by(switch) %>% summarise(
    'Button interactions' = n_distinct(ix_id),
  )
)
dev.off()


# 7 CONTENT PREFERENCE ------------------------------------------------------------------------------------------

df2 <- read.table("parttwo-stimuli-interactions.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE)
df2

content.preference <- df2 %>% group_by(stimulus,content) %>%
  summarise(
    'Activations' = sum(interactions),
    'Activations per monkey' = round(sum(interactions.monkey),2),
    'Mean of activations per monkey' = round(mean(interactions.monkey),2),
    'Interaction time (s)' = round(sum(usetime),2),
    'Interaction time (s) per monkey' = round(sum(usetime.monkey),2),
    'Mean of interaction time per monkey' = round(mean(usetime.monkey),2)
  )
content.preference

png("7-content-preference-1-basics.png",height=300,width=1500)
grid.table(content.preference)
dev.off()

content.preference2 <- df %>% filter(stimulus!='no-stimuli') %>% group_by(stimulus,content) %>% 
  summarise(
    'Mean duration (s)' = round(mean(duration),2),
    'Median duration (s)' = round(median(duration),2),
    'SD of duration (s)' = round(sd(duration),2),
    'Longest duration (s)' = round(max(duration),2),
    'Shortest duration (s)' = round(min(duration),2)
  )

content.preference2

png("7-content-preference-2-durations.png",height=300,width=1500)
grid.table(content.preference2)
dev.off()


# 8 PASSING THROUGH AND SITTING ------------------------------------------------------------------------------------------

df <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, walking_through, sitting)
df

n_distinct(df$period_id)

df %>% filter(walking_through==TRUE) %>% 
  summarise(periods = n_distinct(period_id),
            interactions = n_distinct(ix_id)
            )

df %>% filter(sitting==TRUE) %>% 
  summarise(periods = n_distinct(period_id),
            interactions = n_distinct(ix_id)
  )