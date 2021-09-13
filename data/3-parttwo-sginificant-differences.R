library(tidyverse)
library(rstatix)
library(coin)
library(gridExtra)

# Set directory to where this file resides.
setwd(dirname(rstudioapi::getActiveDocumentContext()$path))

# Load data

# First table
df <- read.table("parttwo-data.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE) %>%
  select(period_id, ix_id, date, study_day, test_phase, test_phase_day, using_stimuli, condition, stimulus, switch, content, starttime, duration, individual)
head(df)

# Change some data types
df$period_id <- as.character(df$period_id)
df$ix_id <- as.character(df$ix_id)
df$switch <- as.factor(df$switch)
df$starttime <- as.character(df$starttime)
df$test_phase_day <- as.factor(df$test_phase_day)

# Data now
head(df)

# Other table to use for comparing stimuli content and interaction zones
df2 <- read.table("parttwo-stimuli-interactions.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE)
head(df2)
df2$switch <- as.factor(df2$switch)

# -- INFO ------------------------------------------------------------------------------------------

# What type of wilxocon test and why?

# # We don't assume the data to follow any normal distribution and thus we are using a nonparametric test, which Wilcox is. --> WHY??
# # Individual monkeys are treated as a group. As a group they went through all the conditions. -> WITHIN-SUBJECTS DESIGN
# # Instead of mathing measurements of individual monkeys, we compare the results of the conditions based on daily values. --> NOT MATCHED, INDEPENDENT
# # These daily values do not correspond to each other. --> INDEPENDENT
# ## ... VALUES ARE NOT PAIRED
# 
# # Wilcoxon rank-sum or signed-rank? Wilcoxon signed-rank test assumes the data is paired: two related samples, matched samples, or 
# # repeated measurements on a single sample (E.g."Is there difference between measurements taken before and after taking a drug?"). 
# # Wilcoxon rank-sum test assumes that two samples are independent. 
# # (E.g. “Is there any significant difference between women and men median weights?”).
# 
# # Wilcoxon rank-sum test (Mann-Whitney U-test) for comparing the significance. 
# # This is done witht he wilcox_test function with parameter *'paired'* set to *'FALSE'*.


# On adjusting p-values

# # When doing pairwise comparison testing, we need to adjust the resulting p-values; 
# # the probability of making a type-I error increases with the number of statistical 
# # tests we are making. Now we are going to make 30 tests because we compare each of 
# # the 6 conditions together (6x5). There are multiple methods for adjusting p-values. 
# # Here we are using a pairwise wilcox test function from rstatix library that takes in
# # a parameter for the chosen adjustment method for p-value.
# # 
# # Example methods to adjusting p-values:
# # 
# # - 'bonferroni' (Bonferroni is apparently quite a coservative method to use)
# # - 'holm' (holm is an updated method from Bonferroni)
# # - 'hochberg'
# # 
# # *Wilcox pairwise signed-rank with rstatix: https://rpkgs.datanovia.com/rstatix/reference/wilcox_test.html*
# # *On adjusting p-values: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6099145/*


# --- Transform data ------------------

# Collect summary data for each study day
data.daily <- df %>% group_by(stimulus, using_stimuli, condition, test_phase, test_phase_day, study_day) %>% 
  summarise(
    periods = n_distinct(period_id),
    interactions = n_distinct(ix_id),
    usetime = sum(duration),
  ) %>% ungroup()

# For calculating mean values over the daily data, 
# we need to add values for any day that did not 
# have any interactions.

# video 2
data.daily <- bind_rows(
  data.daily, list(stimulus='visual', using_stimuli=TRUE, condition='stimuli', 
                   test_phase='5-visual-2', test_phase_day="3", study_day=19, 
                   periods=0, interactions=0, usetime=0))

# audio 3
data.daily <- bind_rows(
  data.daily, list(stimulus='auditory', using_stimuli=TRUE, condition='stimuli', 
                   test_phase='6-audio-3', test_phase_day="3", study_day=22, 
                   periods=0, interactions=0, usetime=0))

# Posterior baseline
data.daily <- bind_rows(
  data.daily, list(stimulus='no-stimulus', using_stimuli=FALSE, condition='second-baseline', 
                   test_phase='8-control-post', test_phase_day="2", study_day=27, 
                   periods=0, interactions=0, usetime=0))


# Arrange the table
data.daily <- data.daily %>% arrange(study_day)
data.daily$condition <- as.factor(data.daily$condition)
data.daily$stimulus <- as.factor(data.daily$stimulus)

head(data.daily)


# --- Significance tests ------------------------

# 1 Stimuli vs no-stimuli-----------------------------------------------------------------------------------

## Summary statistics
tab <- data.daily %>% 
  group_by(condition) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2))

tab

png("figures/significance-tests/1 condition_summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

## Visualising

# The boxplot compactly displays the distribution of a continuous variable. 
# It visualises five summary statistics (the median, two hinges and two whiskers), 
# and all "outlying" points individually.

# The lower and upper hinges correspond to the first and third quartiles (the 25th and 75th percentiles). 
# The upper whisker extends from the hinge to the largest value no further than 1.5 * IQR from the hinge 
# (where IQR is the inter-quartile range, or distance between the first and third quartiles). 
# The lower whisker extends from the hinge to the smallest value at most 1.5 * IQR of the hinge. 
# Data beyond the end of the whiskers are called "outlying" points and are plotted individually.

fig <- data.daily %>%
  ggplot(aes(x=condition, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Troop's daily interaction time (s)") +
  theme_minimal() +
  scale_x_discrete(labels = list('baseline','post-stimuli','stimuli'))
fig

# g2 <- data %>% 
#   group_by(using_stimuli) %>%
#   summarise(usetime=mean(usetime.monkey), se=sd(usetime.monkey)/sqrt(n_distinct(study_day)), 
#             se.min=usetime-se, se.max=usetime+se) %>%
#   ggplot(aes(using_stimuli, usetime)) +
#   geom_bar(stat = "identity", position = "dodge", width = 0.7) +
#   geom_errorbar(aes(ymin=se.min,ymax=se.max, width = 0.3)) +
#   xlab(NULL) +
#   ylab("Daily interaction time per monkey (s)") +
#   theme_minimal() +
#   scale_x_discrete(labels = list('no-stimuli','stimuli')) +
#   labs(
#     caption="Error bars present standard error (SE).")

ggsave("figures/significance-tests/1 condition_boxplot.png", fig, width=3.5, height=4.5)

## Significance of difference with Wilcoxon rank-sum test

results <- tibble(
  cond1=c("first-baseline","first-baseline","stimuli"),
  cond2=c("stimuli","second-baseline","second-baseline"), 
  p=0)

### baseline to stimuli
data <- data.daily %>% filter(condition!='second-baseline')

test <- wilcox_test(
  data$usetime ~ data$condition, 
  alternative='two.sided',
  paired=FALSE,
  detailed=TRUE)

results[1,3] <- round(as.double(pvalue(test)),3)

### stimuli to post-stimuli
data <- data.daily %>% filter(condition!='first-baseline')

test <- wilcox_test(
  data$usetime ~ data$condition, 
  alternative='two.sided',
  paired=FALSE,
  detailed=TRUE)

results[2,3] <- round(as.double(pvalue(test)),3)

### baseline to post-stimuli ("drug effect")
data <- data.daily %>% filter(condition!='stimuli')

test <- wilcox_test(
  data$usetime ~ data$condition, 
  alternative='two.sided',
  paired=FALSE,
  detailed=TRUE)

results[3,3] <- round(as.double(1-pvalue(test)),3)
results

png("figures/significance-tests/1 condition_tests.png",height=100,width=400)
grid.table(results)
dev.off()

remove(test, data, fig, tab, results)

# 2 Audio vs Visual-----------------------------------------------------------------------------------------

## Summary stats
tab <- data.daily %>% filter(stimulus!='no-stimulus') %>%
  group_by(condition, stimulus) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2)) %>% ungroup()

tab

png("figures/significance-tests/2 stimuli-type_summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

## Visualising
fig <- data.daily %>% filter(stimulus!='no-stimulus') %>%
  ggplot(aes(x=stimulus, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Troop's daily interaction time (s)") +
  theme_minimal() 
fig

ggsave("figures/significance-tests/2 stimuli-type_boxplot.png", fig, width=5.0, height=4.5)

## Significance test
data <- data.daily %>% filter(stimulus!='no-stimulus')
test <- wilcox_test(
  data$usetime ~ data$stimulus, 
  alternative='two.sided', 
  paired=FALSE,
  detailed=TRUE)

test

results <- tibble(cond1=c("audio"),cond2=c("visual"),p=0)
results[1,3] <- as.double(1-pvalue(test))
results

png("figures/significance-tests/2 stimuli_type_tests.png",height=100,width=400)
grid.table(results)
dev.off()

remove(results, test, fig, tab)

# 3 Audio to baseline and post-stimuli ---------------------

# Summary stats
data.daily %>% 
  group_by(condition, stimulus) %>%
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2))

# Visualising
data.daily %>% filter(stimulus!="visual") %>%
  ggplot(aes(x=condition, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  scale_x_discrete(labels= list("Baseline", "Post-stimuli", "Audio")) +
  theme_minimal()

# Audio to baseline
data <- data.daily %>% filter(stimulus!='visual') %>% filter(condition!="second-baseline")
wilcox_test(
  data$usetime ~ data$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

# Audio to post-stimuli
data <- data.daily %>% filter(stimulus!='visual') %>% filter(condition!="first-baseline")
wilcox_test(
  data$usetime ~ data$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

remove(data)

# 4 - Stimuli Content----------------

# A - Audio

tab <- df2 %>% filter(stimulus=='auditory') %>% 
  group_by(content) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2))

tab

png("figures/significance-tests/4-A content_audio_summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising
fig <- df2 %>% filter(stimulus=='auditory') %>%
  ggplot(aes(x=content, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time (s)") + 
  theme_minimal()
fig

ggsave("figures/significance-tests/4-A content_audio_boxplot.png", fig, width=5.0, height=4.5)

## Significance tests

results <- tibble(
  cond1=c("music","music","traffic"),
  cond2=c("traffic","rain","rain"),
  p=0)
results

data <- df2 %>% filter(content=="music" | content=="traffic")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[1,3] <- as.double(1-pvalue(test))

data <- df2 %>% filter(content=="music" | content=="rain")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[2,3] <- as.double(1-pvalue(test))

data <- df2 %>% filter(content=="traffic" | content=="rain")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[3,3] <- as.double(1-pvalue(test))

png("figures/significance-tests/4-A content_audio_tests.png",height=100,width=400)
grid.table(results)
dev.off()

remove(data, tab,fig,results,test)

# B - Video ------------------------------

## Summary stats
tab <- df2 %>% filter(stimulus=='visual') %>% 
  group_by(content) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2))

tab

png("figures/significance-tests/4-B content_visual_summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising
fig <- df2 %>% filter(stimulus=='visual') %>%
  ggplot(aes(x=content, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time (s)") +
  theme_minimal()
fig

ggsave("figures/significance-tests/4-B content_visual_boxplot.png", fig, width=5.0, height=4.5)

## Signfiicance tests

results <- tibble(
  cond1=c("underwater","underwater","abstract"),
  cond2=c("abstract","worms","worms"),
  p=0)

data <- df2 %>% filter(content=="underwater" | content=="abstract")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[1,3] <- as.double(1-pvalue(test))

data <- df2 %>% filter(content=="underwater" | content=="worms")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[2,3] <- as.double(1-pvalue(test))

data <- df2 %>% filter(content=="abstract" | content=="worms")
test <- wilcox_test(
  data$usetime ~ data$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[3,3] <- as.double(1-pvalue(test))

results

png("figures/significance-tests/4-B content_visual_tests.png",height=100,width=400)
grid.table(results)
dev.off()

remove(tab,fig,data,results,test)


# 5 - Interactions between zones

## Summary stats
tab <- df2 %>% 
  group_by(switch) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime),2), 
    Median=round(median(usetime),2), 
    SD=round(sd(usetime),2), 
    SE=round(SD/sqrt(N),2))

tab

png("figures/significance-tests/5 zones_summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

## Visualising

fig <- df2 %>%
  ggplot(aes(x=switch, y=usetime)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time (s)") +
  theme_minimal()
fig

ggsave("figures/significance-tests/5 zones_boxplot.png", fig, width=5.0, height=4.5)

## Significance tests

results <- tibble(cond1=c("0","0","1"),cond2=c("1","2","2"),p=0)

data <- df2 %>% filter(switch=="0" | switch=="1")
test <- wilcox_test(
  data$usetime ~ data$switch, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[1,3] <- as.double(pvalue(test))

data <- df2 %>% filter(switch=="0" | switch=="2")
test <- wilcox_test(
  data$usetime ~ data$switch, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[2,3] <- as.double(pvalue(test))


data <- df2 %>% filter(switch=="1" | switch=="2")
test <- wilcox_test(
  data$usetime ~ data$switch, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
results[3,3] <- as.double(pvalue(test))

results

png("figures/significance-tests/5 zones_tests.png",height=100,width=400)
grid.table(results)
dev.off()

remove(tab,fig,data,results,test)

