library(tidyverse)
library(rstatix)
library(coin)
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

df2 <- read.table("parttwo-stimuli-interactions.csv", header = T, sep = ",", dec = ".", stringsAsFactors = TRUE)
df2

monkeys=3

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



# Data ------------------------------------------------------------------------------------------------

# Collect summary data for each study day
data.daily <- df %>% group_by(stimulus, using_stimuli, condition, test_phase, test_phase_day, study_day) %>% 
  summarise(.groups='drop',
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


# 1 Stimuli vs no-stimuli-----------------------------------------------------------------------------------
# Data: daily interaction time by monkey (usetime.monkey), by stimuli condition (using_stimuli)

data <- data.daily %>% filter(condition!='second-baseline') %>% select(condition, study_day, usetime.monkey)
data$condition <- as.factor(data$condition)

data

# Summary stats
tab <- data %>% 
  group_by('Condition'=condition) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

tab

png("significance-tests/stimuli-effect/summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising

# The boxplot compactly displays the distribution of a continuous variable. 
# It visualises five summary statistics (the median, two hinges and two whiskers), 
# and all "outlying" points individually.

# The lower and upper hinges correspond to the first and third quartiles (the 25th and 75th percentiles). 
# The upper whisker extends from the hinge to the largest value no further than 1.5 * IQR from the hinge 
# (where IQR is the inter-quartile range, or distance between the first and third quartiles). 
# The lower whisker extends from the hinge to the smallest value at most 1.5 * IQR of the hinge. 
# Data beyond the end of the whiskers are called "outlying" points and are plotted individually.

g1 <- data %>%
  ggplot(aes(x=condition, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal() +
  scale_x_discrete(labels = list('baseline','stimuli'))
g1

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

ggsave("significance-tests/stimuli-effect/boxplot.png", g1, width=3.5, height=4.5)


## Significance of difference with Wilcoxon rank-sum test

test1.1 <- wilcox_test(
  data$usetime.monkey ~ data$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

test1.1

## Signed-rank (do also signed rank test to compare "drug")

data <- data.daily %>% filter(using_stimuli==FALSE) %>% select(test_phase, usetime.monkey)
data$test_phase <- as.factor(data$test_phase)

test1.2 <- wilcox_test(
  data$usetime.monkey ~ data$test_phase, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=TRUE,
  detailed=TRUE)

test1.2

# Comparing baselines and stimuli --------------------------------------------------------------------------------

data <- data.daily %>% select(condition, study_day, usetime.monkey)
data$condition <- as.factor(data$condition)

# Summary stats
tab <- data %>% 
  group_by(condition) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

tab

png("significance-tests/stimuli-effect/summary-stats-baselines.png",height=100,width=400)
grid.table(tab)
dev.off()

g1 <- data %>%
  ggplot(aes(x=condition, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal() +
  scale_x_discrete(labels = list('baseline','post-stimuli','stimuli'))

g1

ggsave("significance-tests/stimuli-effect/baselines-boxplot.png", g1, width=3.5, height=4.5)

results.baselines <- tibble(cond1=c("first-baseline","first-baseline","stimuli"),cond2=c("stimuli","second-baseline","second-baseline"),p=0)
results.baselines

d <- data %>% filter(condition!='stimuli')
test <- wilcox_test(
  d$usetime.monkey ~ d$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

results.baselines[1,3] <- as.double(pvalue(test))
results.baselines


d <- data %>% filter(condition!='first-baseline')
test <- wilcox_test(
  d$usetime.monkey ~ d$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

results.baselines[2,3] <- as.double(pvalue(test))
results.baselines

d <- data %>% filter(condition!='second-baseline')
test <- wilcox_test(
  d$usetime.monkey ~ d$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)
results.baselines[3,3] <- as.double(1-pvalue(test))
results.baselines

png("significance-tests/stimuli-effect/baselines-sigs.png",height=100,width=400)
grid.table(results.baselines)
dev.off()


# 2 Audio vs Visual-----------------------------------------------------------------------------------------

data <- data.daily %>% filter(condition!='second-baseline') %>% select(stimulus, study_day, usetime.monkey)
data$stimulus <- as.factor(data$stimulus)

data

# Summary stats
tab <- data %>% 
  group_by(stimulus) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

tab

png("significance-tests/stimuli-type/summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising
g1 <- data %>%
  ggplot(aes(x=stimulus, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal() +
  scale_x_discrete(labels = list('audio','baseline','visual'))
g1

ggsave("significance-tests/stimuli-type/boxplot.png", g1, width=5.0, height=4.5)

## Significance of difference with Wilcoxon rank-sum test
### pairwise, with p.adj method

test2.1 <- pairwise_wilcox_test(data,
  usetime.monkey ~ stimulus, 
    p.adjust.method = 'holm', 
    alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
    paired=FALSE,
    detailed=TRUE)

tab <- test2.1 %>% select(group1, group2, statistic, p, p.adj, p.adj.signif)
tab

png("significance-tests/stimuli-type/wilcoxon-pairwise-rank-sum.png",height=100,width=400)
grid.table(tab)
dev.off()


### Just audio vs visual
data <- data %>% filter(stimulus!='no-stimulus')
data

test2.2 <- wilcox_test(
  data$usetime.monkey ~ data$stimulus, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)

test2.2

# XXX Audio to baseline weeks -----------------------------------------------------------------------------------------

data <- data.daily %>% filter(stimulus != 'visual') %>% select(condition, study_day, usetime.monkey)
data$condition <- as.factor(data$condition)

data

# Summary stats
data %>% 
  group_by(condition) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

# Visualising
data %>%
  ggplot(aes(x=condition, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal()


d <- data %>% filter(condition!='stimuli')

wilcox_test(
  d$usetime.monkey ~ d$condition, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE)


# 3 Stimuli Content-----------------------------------------------------------------------------------------

# Data
df2

# A - AUDIO - summary stats and visualisation

data <- df2 %>% filter(stimulus=='auditory')
data

tab <- data %>% 
  group_by(content) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

tab

png("significance-tests/stimuli-content/audio-summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising
g1 <- data %>%
  ggplot(aes(x=content, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") + 
  theme_minimal()
g1

ggsave("significance-tests/stimuli-content/audio-boxplot.png", g1, width=5.0, height=4.5)

#----------------------------------------------------------------------------------------------------------------------------------

results.audio <- tibble(cond1=c("music","music","traffic"),cond2=c("traffic","rain","rain"),p=0)
results.audio

d <- data %>% filter(content=="music" | content=="traffic")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.audio[1,3] <- as.double(1-pvalue(test))
results.audio

d <- data %>% filter(content=="music" | content=="rain")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.audio[2,3] <- as.double(1-pvalue(test))
results.audio

d <- data %>% filter(content=="traffic" | content=="rain")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.audio[3,3] <- as.double(1-pvalue(test))
results.audio

png("significance-tests/stimuli-content/audio-sig-tests.png",height=100,width=400)
grid.table(results.audio)
dev.off()


# B - VIDEO - summary stats and visualisation--------------------------------------------------------

data <- df2 %>% filter(stimulus=='visual')
data

# Summary stats
tab <- data %>% 
  group_by(content) %>% 
  summarise(
    N = n_distinct(study_day),
    Mean=round(mean(usetime.monkey),2), 
    Median=round(median(usetime.monkey),2), 
    SD=round(sd(usetime.monkey),2), 
    SE=round(SD/sqrt(N),2))

tab

png("significance-tests/stimuli-content/video-summary-stats.png",height=100,width=400)
grid.table(tab)
dev.off()

# Visualising
g1 <- data %>%
  ggplot(aes(x=content, y=usetime.monkey)) +
  geom_boxplot(outlier.colour = "red", outlier.shape = 1) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal()
g1

g2 <- data %>% 
  group_by(content) %>%
  summarise(usetime=mean(usetime.monkey), se=sd(usetime.monkey)/sqrt(n_distinct(study_day)), 
            se.min=usetime-se, se.max=usetime+se) %>%
  ggplot(aes(content, usetime)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.7) +
  geom_errorbar(aes(ymin=se.min,ymax=se.max, width = 0.3)) +
  xlab(NULL) +
  ylab("Daily interaction time per monkey (s)") +
  theme_minimal() +
  labs(
    caption="Error bars present standard error (SE).")
g2

ggsave("significance-tests/stimuli-content/video-boxplot.png", g1, width=5.0, height=4.5)
ggsave("significance-tests/stimuli-content/video-barplot.png", g2, width=5.0, height=4.5)  

#----------------------------------------------------------------------------------------------------------------------------------

results.video <- tibble(cond1=c("underwater","underwater","abstract"),cond2=c("abstract","worms","worms"),p=0)
results.video

d <- data %>% filter(content=="underwater" | content=="abstract")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.video[1,3] <- as.double(1-pvalue(test))
results.video

d <- data %>% filter(content=="underwater" | content=="worms")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.video[2,3] <- as.double(1-pvalue(test))
results.video

d <- data %>% filter(content=="abstract" | content=="worms")
test <- wilcox_test(
  d$usetime.monkey ~ d$content, 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)
test
results.video[3,3] <- as.double(1-pvalue(test))
results.video


png("significance-tests/stimuli-content/video-sig-tests.png",height=100,width=400)
grid.table(results.video)
dev.off()

#----------------------------------------------------------------------------------------------------------------------------------
# Significance of difference with Wilcoxon rank-sum test
# pairwise, with p.adj method

test3.1 <- pairwise_wilcox_test(
  df2,
  usetime.monkey ~ content, 
  p.adjust.method = 'holm', 
  alternative='two.sided', # we look into whether group1 has either smaller or larger values than group2, not only one of them.
  paired=FALSE,
  detailed=TRUE
)

test3.1
tab <- test3.1 %>% select(group1, group2, statistic, p, p.adj, p.adj.signif)
tab

png("significance-tests/stimuli-content/wilcoxon-pairwise-rank-sum.png",height=400,width=400)
grid.table(tab)
dev.off()


