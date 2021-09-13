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

# Data now
head(df)

# 1 - Test skew of the duration of interactions

## Test
agostino.test(df$duration, "two.sided") # test with all the interactions and the simple duration

## Plot
ggplot(df, aes(duration)) + 
  geom_density() + 
  labs(title='Skew of interaction durations over all conditions')


# 2 - Skew of daily interaction time per monkey

## Data
data.skew <- df %>% group_by(study_day) %>% 
  summarise(
    usetime.daily = sum(duration)
  )

## Add missing values
data.skew <- bind_rows(data.skew, list(study_day=19, usetime.daily=0))
data.skew <- bind_rows(data.skew, list(study_day=22, usetime.daily=0))
data.skew <- bind_rows(data.skew, list(study_day=27, usetime.daily=0))

## Summary data
data.skew %>% summarise(
  mean(usetime.daily),
  sd(usetime.daily)
)

## Test
agostino.test(data.skew$usetime.daily, "two.sided")

## Plot
ggplot(data.skew, aes(usetime.daily)) + 
  geom_density() + 
  labs(title='Skew of daily interaction time over all conditions')
