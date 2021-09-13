
# There were 3 monkeys
# The study period was 32 days

library(tidyverse)
library(gridExtra)
library(Kendall) # for testing trend in time-series data

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

# Let's peek
head(df)

# --------- TRANSFORM DATA -----------------------

# 1 - Daily summary data ---------------

# Collect summary data for each study day
df.daily <- df %>% 
  group_by(stimulus, using_stimuli, condition, test_phase, test_phase_day, study_day) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = n_distinct(ix_id),
    usetime = sum(duration),
  ) %>% ungroup()

# For calculating mean values over the daily data, 
# we need to add values for any day that did not 
# have any interactions.

# Cycle: visual 2
df.daily <- bind_rows(
  df.daily, list(stimulus='visual', using_stimuli=TRUE, condition='stimuli', 
                 test_phase='5-visual-2', test_phase_day="3", study_day=19, 
                 periods=0, interactions=0, usetime=0))

# Cycle: audio 3
df.daily <- bind_rows(
  df.daily, list(stimulus='auditory', using_stimuli=TRUE, condition='stimuli', 
                 test_phase='6-audio-3', test_phase_day="3", study_day=22, 
                 periods=0, interactions=0, usetime=0))

# Posterior baseline
df.daily <- bind_rows(
  df.daily, list(stimulus='no-stimulus', using_stimuli=FALSE, condition='second-baseline', 
                 test_phase='8-control-post', test_phase_day="2", study_day=27, 
                 periods=0, interactions=0, usetime=0))

# Arrange the table
df.daily <- df.daily %>% arrange(study_day)

head(df.daily)

# 2 - Data grouped by interactivity periods -----

# Group the data by the interactive periods. 
#   Calculate the duration of period by sum of its interaction durations. 
#   Pick the starttime as the earliest time of its interactions.
df.periods <- df %>% 
  group_by(period_id, date, study_day, test_phase, 
           test_phase_day, stimulus, individual, using_stimuli, condition) %>%
  summarise(
    interactions = n_distinct(ix_id),
    starttime = min(starttime),
    duration = sum(duration)
  ) %>% ungroup()

# Let's peek
head(df.periods)

# The original data is by interactions. Let's just rename it for later use.
df.interactions <-  df

remove(df)

# --------- ANALYSIS ------------------------------

# 0 - Trend test ------------------------
# Is there a trend in the data distribution of daily interaction time?
# (it looks like the data follows a cyclic or zigzag pattern)
# Trend test: testing whether there is a trend in visible "cycles" over the study 
MannKendall(df.daily$usetime)

# 1 - Sumary stats -----------------------

# Interactive periods: total and daily
# (Zone) Interactions: total and daily
# Interaction time (usetime): total, daily and SD

# A - Whole study

tab <- df.daily %>% summarise(
  'Interactive periods' = sum(periods),
  'Zone interactions' = sum(interactions),
  'Total interaction time' = sum(usetime),
  'Daily interactive periods' = mean(periods),
  'Daily zone interactions' = format(round(mean(interactions),2),nsmall=2),
  'Daily interaction time' = format(round(mean(usetime),2),nsmall=2)
)
tab

png("figures/basics/1-A summary_whole-study.png",height=100,width=900)
grid.table(tab)
dev.off()

# B - Condition (Baseline or stimuli)

tab <- df.daily %>% group_by(using_stimuli) %>% 
  summarise(
    # Total values:
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Zone Interactions' = sum(interactions),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    # Comparable daily values (as there are different number of test days):
    'Interactive periods daily' = format(round(mean(periods),2),nsmall=2),
    'Zone Interactions daily' = format(round(mean(interactions),2),nsmall=2),
    'Interaction time (s) daily' = format(round(mean(usetime),2),nsmall=2),
    'SD of interaction time (s) daily' = format(round(sd(usetime),2),nsmall=2)
  ) %>% ungroup()

tab

png("figures/basics/1-B summary_using-stimuli.png",height=150,width=1600)
grid.table(tab)
dev.off()

# C - Stimuli type (audio, visual, no-stimuli)

tab <- df.daily %>% group_by(stimulus) %>% 
  summarise(
    # Total values:
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Zone Interactions' = sum(interactions),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    # Comparable daily values (as there are different number of test days):
    'Interactive periods daily' = format(round(mean(periods),2),nsmall=2),
    'Zone Interactions daily' = format(round(mean(interactions),2),nsmall=2),
    'Interaction time (s) daily' = format(round(mean(usetime),2),nsmall=2),
    'SD of interaction time (s) daily' = format(round(sd(usetime),2),nsmall=2)
  ) %>% ungroup()

tab

png("figures/basics/1-C summary_stimuli-type.png",height=150,width=1600)
grid.table(tab)
dev.off()

# D - Study cycles

tab <- df.daily %>% group_by(test_phase) %>% 
  summarise(
    # Total values:
    'Study days' = n_distinct(study_day),
    'Interactive periods' = sum(periods),
    'Zone Interactions' = sum(interactions),
    'Interaction time (s)' = format(round(sum(usetime),2),nsmall=2),
    # Comparable daily values (as there are different number of test days):
    'Interactive periods daily' = format(round(mean(periods),2),nsmall=2),
    'Zone Interactions daily' = format(round(mean(interactions),2),nsmall=2),
    'Interaction time (s) daily' = format(round(mean(usetime),2),nsmall=2),
    'SD of interaction time (s) daily' = format(round(sd(usetime),2),nsmall=2)
  ) %>% ungroup()

tab

png("figures/basics/1-D summary_cycles.png",height=300,width=1600)
grid.table(tab)
dev.off()

# Clean up
remove(tab)


# 2 - Duration of interactivity periods ------------

# Collect the stats about interactive period durations: 
#   Mean, median, std, longest, shortest

# A - Whole study

tab <- df.periods %>% 
  summarise(
    'Mean duration' = format(round(mean(duration),2), nsmall=2),
    'Median duration' = format(round(median(duration),2), nsmall=2),
    'SD of duration' = format(round(sd(duration),2), nsmall=2),
    'Longest duration' = format(round(max(duration),2),nsmall=2),
    'Shortest duration' = format(round(min(duration),2), nsmall=2)
  )
tab

png("figures/basics/2-A duration_whole-study.png",height=100,width=600)
grid.table(tab)
dev.off()

# B - Condition (baseline or stimuli)

tab <- left_join(
  df.daily %>% 
    group_by(using_stimuli) %>%
    summarise('Interactive periods' = sum(periods),
              'Interactive periods daily' = format(round(mean(periods),2), nsmall=2)
    ) %>% ungroup(), 
  df.periods %>% 
    group_by(using_stimuli) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)
tab

png("figures/basics/2-B duration_using-stimuli.png",height=150,width=900)
grid.table(tab)
dev.off()

# C - Stimuli type (audio, visual, no-stimuli)

tab <- left_join(
  df.daily %>% 
    group_by(stimulus) %>%
    summarise(
      'Interactive periods' = sum(periods),
      'Interactive periods daily' = format(round(mean(periods),2), nsmall=2)
    ) %>% ungroup(), 
  df.periods %>% group_by(stimulus) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)

tab

# Print out the results table. Saved to the same directory as the file is at.
png("figures/basics/2-C duration_stimuli-type.png",height=150,width=900)
grid.table(tab)
dev.off()

# D - Study cycles

tab <- left_join(
  df.daily %>% 
    group_by(test_phase) %>%
    summarise(
      'Interactive periods' = sum(periods),
      'Interactive periods daily' = format(round(mean(periods),2), nsmall=2)
    ) %>% ungroup(), 
  df.periods %>% group_by(test_phase) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)

tab

# Print out the results table. Saved to the same directory as the file is at.
png("figures/basics/2-D duration_cycles.png",height=300,width=900)
grid.table(tab)
dev.off()

remove(tab)

# 3 - Duration of zone interactions ---------------------

# A - Whole study
df.interactions
tab <- df.interactions %>% summarise(
  'Mean duration' = format(round(mean(duration),2), nsmall=2),
  'Median duration' = format(round(median(duration),2), nsmall=2),
  'SD of duration' = format(round(sd(duration),2), nsmall=2),
  'Longest duration' = format(round(max(duration),2),nsmall=2),
  'Shortest duration' = format(round(min(duration),2), nsmall=2)
)

tab

png("figures/basics/3-A duration_whole-study.png",height=100,width=600)
grid.table(tab)
dev.off()

# B - Condition (Baseline or stimuli)

tab <- left_join(
  df.daily %>% 
    group_by(using_stimuli) %>%
    summarise(
      'Zone interactions' = sum(interactions),
      'Daily zone interactions' = format(round(mean(interactions),2), nsmall=2)
    ) %>% ungroup(), 
  df.interactions %>% 
    group_by(using_stimuli) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)

tab

png("figures/basics/3-B duration_using-stimuli.png",height=120,width=920)
grid.table(tab)
dev.off()

# C - Stimuli type (audio, visual, no-stimuli)

tab <- left_join(
  df.daily %>% 
    group_by(stimulus) %>%
    summarise(
      'Zone interactions' = sum(interactions),
      'Daily zone interactions' = format(round(mean(interactions),2), nsmall=2)
    ) %>% ungroup(), 
  df.interactions %>% group_by(stimulus) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)

tab

png("figures/basics/3-C duration_stimuli-type.png",height=150,width=920)
grid.table(tab)
dev.off()

# D - Study cycles

tab <- left_join(
  df.daily %>% 
    group_by(test_phase) %>%
    summarise(
      'Zone interactions' = sum(interactions),
      'Daily Zone interactions' = format(round(mean(interactions),2), nsmall=2)
    ) %>% ungroup(), 
  df.interactions %>% group_by(test_phase) %>% 
    summarise(
      'Mean duration' = format(round(mean(duration),2), nsmall=2),
      'Median duration' = format(round(median(duration),2), nsmall=2),
      'SD of duration' = format(round(sd(duration),2), nsmall=2),
      'Longest duration' = format(round(max(duration),2),nsmall=2),
      'Shortest duration' = format(round(min(duration),2), nsmall=2)
    ) %>% ungroup()
)

tab

png("figures/basics/3-D duration_cycles.png",height=300,width=900)
grid.table(tab)
dev.off()

remove(tab)


# 4 - Trajectory of interaction time over the study period -----

# Plot the troop's daily interaction time

# A - By study days 

fig <- ggplot(data=df.daily, aes(study_day, usetime)) + 
  geom_col(aes(fill=stimulus)) +
  geom_smooth(se=FALSE, colour="black") +
  scale_x_continuous(breaks=seq(1,32,1)) +
  scale_y_continuous(breaks=seq(0,70,5)) +
  xlab('Study day') +
  ylab("Troop's interaction time (s)") +
  theme_minimal()

fig <- fig + theme(panel.grid.minor = element_blank()) + 
  theme(panel.grid.major = element_blank()) +
  scale_fill_brewer("Condition:", palette="Set2") + 
  theme(legend.position = "top")

fig
ggsave("figures/basics/4-A trajectory.png", fig, width=7.5, height=4.0)

remove(fig)

# B - By cycles

boxplot <- ggplot(data=df.daily,aes(test_phase, usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1, aes(fill=stimulus)) +
  scale_y_continuous(breaks=seq(0,70,5)) +
  xlab(NULL) +
  ylab("Troop's interaction time per day (s)") +
  scale_x_discrete(labels = list("Baseline", "Audio", "Visual", "Audio", "Visual", "Audio", "Visual", "Post-stimuli")) +
  labs(caption = "\nMiddle lines = median; hinges = 25th and 75th percentiles; whiskers = max and min values") +
  theme_minimal()

boxplot <- boxplot + 
  theme(panel.grid.minor = element_blank()) + 
  theme(panel.grid.major = element_blank()) +
  scale_fill_brewer("Condition:", palette="Set2") +
  theme(legend.position = "top")

boxplot

ggsave("figures/basics/4-B boxplot_cycles.png", boxplot, width=7.0, height=4.0)  

remove(boxplot)

# 5 - Interactive periods by individual monkeys ------------------

# A - Whole study

tab <- df.periods %>% 
  group_by(individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  ) %>% ungroup()

tab

png("figures/basics/5-A individuals_whole-study.png",height=150,width=800)
grid.table(tab)
dev.off()

# B - Condition (baseline or stimuli)

tab <- df.periods %>% 
  group_by(using_stimuli, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  ) %>% ungroup()

tab

png("figures/basics/5-B individuals_using-stimuli.png",height=150,width=800)
grid.table(tab)
dev.off()

# C - Stimuli type (audio, visual, no-stimuli)

tab <- df.periods %>% group_by(stimulus, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  ) %>% ungroup()
tab

png("figures/basics/5-C individuals_stimuli-type.png",height=250,width=800)
grid.table(tab)
dev.off()

# D - Study cycles

tab <- df.periods %>% group_by(test_phase, individual) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = sum(interactions),
    usetime = format(round(sum(duration),0),nsmall=0),
    m.duration = format(round(mean(duration),1), nsmall=1),
    md.duration = round(median(duration),1),
    std.duration = format(round(sd(duration),1), nsmall=1),
    max.duration = format(round(max(duration),1),nsmall=1),
    min.duration = format(round(min(duration),1), nsmall=1)
  )

tab

png("figures/basics/5-D individuals-cycles.png",height=450,width=800)
grid.table(tab)
dev.off()

remove(tab)


# 6 - Interactions with zones 1-3 ----------------------

# A - Total
tab <- df.interactions %>% 
  group_by(switch) %>% 
  summarise(
    'Zone interactions' = n_distinct(ix_id)
  ) %>% ungroup()
tab

png("figures/basics/6-A Zone-usage_total.png",height=150,width=300)
grid.table(tab)
dev.off()

# B - By individual
tab <- df.interactions %>% 
  group_by(switch, individual) %>% 
  summarise(
    'Zone interactions' = n_distinct(ix_id)
  ) %>% ungroup()
tab

png("figures/basics/6-B Zone-usage_individual.png",height=250,width=300)
grid.table(tab)
dev.off()

remove(tab)

# 7 Content preference ------------------------------------------------------------------------------------------

condition_length = 9 # (3 zones x 3 days cycle)

tab <- df.interactions %>% filter(stimulus!='no-stimulus') %>% group_by(stimulus,content) %>% 
  summarise(
    'Activations' = n_distinct(ix_id),
    'Activations per day' = round(n_distinct(ix_id)/condition_length,2),
    'Interaction time' = sum(duration),
    'Interaction time per day' = round(sum(duration)/condition_length,2),
    'Mean duration' = round(mean(duration),2),
    'Median duration' = round(median(duration),2),
    'SD of duration' = round(sd(duration),2),
    'Longest duration' = round(max(duration),2),
    'Shortest duration' = round(min(duration),2)
  )

tab

png("figures/basics/7 content-preference.png",height=300,width=1500)
grid.table(tab)
dev.off()

remove(tab, condition_length)

# 8 - Behaviours (walking through or sitting) -------------------------

df.behaviours <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, walking_through, sitting)

tab <- df.behaviours %>% group_by(walking_through, sitting) %>% 
  summarise(periods = n_distinct(period_id),
            interactions = n_distinct(ix_id)
            )

png("figures/basics/8 Behaviours.png",height=200,width=500)
grid.table(tab)
dev.off()

remove(df.behaviours, tab)

# 9 - Interaction time by the hour of the day --------------------

df <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", 
                 stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, date, study_day, using_stimuli, stimulus, 
         test_phase, test_phase_day, start_hour, duration, individual)
df$period_id <- as.character(df$period_id)
df$ix_id <- as.character(df$ix_id)

# B - Whole study

## Raw data
tab <- df %>% 
  group_by(start_hour) %>% # Summarise over test weeks and each hour of the day..
  summarise(
    usetime.hour = sum(duration),
    periods.hour = n_distinct(period_id),
  ) %>% arrange(start_hour) %>% ungroup()

tab

png("figures/basics/9-A hourly-interactions_whole-study.png",height=500,width=400)
grid.table(tab)
dev.off()

# Barplot
fig <- ggplot(data=tab, aes(start_hour, usetime.hour)) + 
  geom_col() +
  ylab("Cumulative interaction time") +
  xlab("Hour of the day") + 
  scale_x_continuous(breaks=seq(4,18,1)) +
  theme_minimal()

fig

ggsave("figures/basics/9-A hourly-interactions_whole-study_barplot.png", fig, width=6.0, height=4.0)

remove(fig)

# In order to create a graph that presents the porportional values of 
# each hour of the day for a given measure (i.e. how big proportion of 
# interactions happened at 6AM during the test week?), we need to also
# obtain the reference value, the total values over the test week to
# what to compare to. 

df.hourly <- df.hourly %>%
  group_by(stimulus) %>%
  summarise(
    tot.usetime = sum(usetime.hour), # The total avg. duration of use over the test week per monkey
    tot.periods = sum(periods.hour) # The total interactions over the test week per monkey
  ) %>% left_join(df.hourly, ., by='stimulus')

# Dotplot with a fitted 
fig <- df.hourly %>%
  ggplot(data=., aes(x=start_hour, y=usetime.hour/tot.usetime)) +
  geom_point() +
  geom_smooth(method=loess,se=FALSE) +
  xlab('Start hour') +
  ylab(NULL) +
  scale_x_continuous(breaks=seq(0,24,1), limits=c(5,17)) +
  #scale_y_continuous(limits=c(0,0.5)) +
  theme_minimal()

fig

ggsave("figures/basics/9-A hourly-interactions_whole-study_trend.png", fig, width=6.0, height=4.0)

# B - By stimuli type
tab <- df %>% 
  group_by(stimulus, start_hour) %>% # Summarise over test weeks and each hour of the day..
  summarise(
    usetime.hour = sum(duration),
    periods.hour = n_distinct(period_id),
  ) %>% arrange(stimulus, start_hour) %>% ungroup()

tab

png("figures/basics/9-B hourly-interactions_stimuli-type.png",height=700,width=400)
grid.table(tab)
dev.off()

remove(df, tab, fig, df.hourly)