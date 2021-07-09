library(tidyverse)
library(gridExtra)
library(lubridate)
library(moments) # D'Agostino test for skew


# Set directory to where this file resides.
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Load data
df <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, date, study_day, using_stimuli, stimulus, test_phase, test_phase_day, start_hour, duration, individual)
df

# What are the data types of columns?
str(df)

# Change some data types
df$period_id <- as.character(df$period_id)
df$ix_id <- as.character(df$ix_id)
df$start_hour <- as.character(start_hour)

# Data now
head(df)


# BASIC VALUES
monkeys = 3
study_days = 32

# 1 TESTING SOME SKEWS --------------------------------------------------------------------------

## Test skew of the duration of interactions
agostino.test(df$duration, "two.sided") # test with all the interactions and the simple duration
ggplot(df, aes(duration)) + 
  geom_density() + 
  labs(title='Skew of interaction durations over all conditions')

## Skew of daily interaction time per monkey
data.skew <- df %>% group_by(study_day) %>% 
  summarise(
    usetime.daily = sum(duration),
    usetime.daily.monkey = usetime.daily/monkeys
  )
data.skew

data.skew <- bind_rows(data.skew, list(study_day=19, usetime.daily=0, usetime.daily.monkey=0))
data.skew <- bind_rows(data.skew, list(study_day=27, usetime.daily=0, usetime.daily.monkey=0))

agostino.test(data.skew$usetime.daily.monkey, "two.sided")
ggplot(data.skew, aes(usetime.daily.monkey)) + 
  geom_density() + 
  labs(title='Skew of daily use time over all conditions')

data.skew %>% summarise(
  mean(usetime.daily.monkey),
  sd(usetime.daily.monkey)
)


# 2 HOURLY USAGE ------------------------------------------------------------------------------

df.hourly <- df %>% 
  group_by(stimulus, start_hour) %>% # Summarise over test weeks and daytime hours...
  summarise(
    usetime.hour = sum(duration),
    usetime.hour.monkey = usetime.hour/monkeys,
    periods.hour = n_distinct(period_id),
    periods.hour.monkey = periods.hour/monkeys
  ) %>% arrange(stimulus, start_hour)

# We see now values that are collected from multiple days of the test week, but based on the hour of the start time of interactions.
head(df.hourly)


# In order to create a graph that presents the porportional values of 
# each hour of the day for a given measure (i.e. how big proportion of 
# interactions happened at 6AM during the test week?), we need to also
# obtain the reference value, the total values over the test week to
# what to compare to. 
#   NOTE: I don't understand why, but the weekly usetime per monkey is 
#   different here when calculated via hours than earlier when calculating via days
#   Total adds up but there is shift in values between weeks 3,4 and 5.
#   More detailed looked into the differences in the end.
df.hourly <- df.hourly %>%
  group_by(stimulus) %>%
  summarise(
    tot.usetime.monkey = sum(usetime.hour.monkey), # The total avg. duration of use over the test week per monkey
    tot.periods.monkey = sum(periods.hour.monkey) # The total interactions over the test week per monkey
  ) %>% left_join(df.hourly, ., by='stimulus')

df.hourly


g.hourly <- df.hourly %>%
  ggplot(data=., aes(x=start_hour, y=usetime.hour.monkey/tot.usetime.monkey)) +
  geom_point() +
  geom_smooth(method=loess,se=FALSE) +
  xlab('Start hour') +
  ylab(NULL) +
  scale_x_continuous(breaks=seq(0,24,1), limits=c(5,17)) +
  #scale_y_continuous(limits=c(0,0.5)) +
  theme_minimal()

g.hourly

ggsave("skew-and-hourly-usage/hourly-usage.png", g.hourly, width=6.0, height=6.0)  


# Generate plots using data from different test weeks separately.

g <- df.hourly %>% subset(stimulus=='no-stimulus') %>% 
  ggplot(data=., aes(x=start_hour, y=usetime.hour.monkey/tot.usetime.monkey)) +
  geom_point() +
  geom_smooth(method=loess,se=FALSE) +
  xlab('Start hour') +
  ylab(NULL) +
  scale_x_continuous(breaks=seq(0,24,1), limits=c(5,17))
  #scale_y_continuous(limits=c(0,0.5))

plot <- g + labs(subtitle='No stimulus')
plot


g$data <- df.hourly %>% subset(stimulus=='auditory')
plot <- g + labs(subtitle='Audio')
plot

g$data <- df.hourly %>% subset(stimulus=='visual')
plot <- g + labs(subtitle='Visual')
plot

