# Load required libraries
library(ggplot2)  # For data visualization
library(dplyr)  # For data manipulation
library(ggpubr)  # For publication-ready themes in ggplot2

#------------------------------------------------------------
# 1. Set Working Directory and Load NEON Data
#------------------------------------------------------------

# Set working directory to the path where the project files are stored
setwd("/user/beetles_intake") #path anonymized

# Define NEON data product ID for beetle data
Beetle_dpID <- "DP1.10022.001"

# Load NEON API token for accessing the data
NEON_TOKEN <- read.delim("/user/Token", header = FALSE)[1, 1]  # Read in the NEON API token path anonymized

# Load the beetle data from NEON API using the 'neonUtilities' package
NEON_df <- neonUtilities::loadByProduct(
  dpID = Beetle_dpID,  # Data product ID for beetles
  site = "PUUM",  # Specify the site (PUUM is one of the NEON sites)
  token = NEON_TOKEN,  # API token for accessing the NEON data
  include.provisional = TRUE,  # Include provisional data (Must for PUUM)
  check.size = FALSE  # Do not check the file size
)

# Extract taxonomist IDs for further analysis
Neon_para <- NEON_df$bet_parataxonomistID  # Parataxonomist IDs from NEON data
Neon_expert <- NEON_df$bet_expertTaxonomistIDProcessed  # Expert taxonomist IDs from NEON data

#filter out parataxonomist IDs that were later re-IDed by experts
neon_para_clean <- Neon_para %>%
  filter(!(individualID %in% Neon_expert$individualID))
# Find common columns between the two dataframes
common_cols <- intersect(names(neon_para_clean), names(Neon_expert))

# Subset dataframes to the common columns
neon_para_common <- neon_para_clean[, common_cols]
neon_expert_common <- Neon_expert[, common_cols]

#Add a column to specify the identifier type
neon_para_common$ID_status<-"para"
neon_expert_common$ID_status<-"expert"

# Row bind the two dataframes to create on harmonized reference
combined_data <- bind_rows(neon_para_common, neon_expert_common)
head(combined_data)
str(combined_data)

table(combined_data$scientificName)

#------------------------------------------------------------
# 2. Create Code Key for Species in PUUM Dataset
#------------------------------------------------------------

# Create a key for taxon codes, associating taxon IDs with scientific names in the PUUM set
code_key <- Neon_expert %>%
  group_by(scientificName) %>%  # Group by scientific name to create a unique mapping
  slice(1) %>%  # Take the first row for each group
  ungroup()

# Convert the code key to a data frame and trim taxon IDs by cutting off numbers at the end
code_key <- as.data.frame(code_key[, c("taxonID", "scientificName")])
code_key$taxonID <- substr(code_key$taxonID, 1, 6)  # Remove extra characters from taxon IDs

# Add an extra species that wasn't recorded in the NEON dataset but was included in a preliminary sample
code_key <- rbind(code_key, c("MECGAG", "Mecyclothorax gagnei"))

#------------------------------------------------------------
# 3. Load and Merge Metadata for PUUM Dataset
#------------------------------------------------------------

# Load metadata for the cleaned beetle images in the PUUM dataset
meta_PUUM <- read.csv("./data/canon_Images_Clean.csv")
head(meta_PUUM)  # View the first few rows of the metadata

# Check for duplicate BeetleIDs (some images are duplicated)
table(duplicated(meta_PUUM$BeetleID))  # Output count of duplicated BeetleIDs

# Merge the cleaned metadata with the code key based on species codes (taxonID)
meta_PUUM <- merge(meta_PUUM, code_key, by.x = "Species", by.y = "taxonID", all.x = TRUE, all.y = FALSE)
head(meta_PUUM)  # View the first few rows of the merged metadata

# Remove duplicate beetle images, keeping only one entry per BeetleID
unique_beetle <- meta_PUUM %>%
  group_by(BeetleID) %>%  # Group by BeetleID to identify duplicates
  slice(1) %>%  # Keep only the first occurrence of each BeetleID
  ungroup()

# Check dimensions and species distribution in the unique beetle dataset
dim(meta_PUUM)
dim(unique_beetle)  # Should show 1580 beetle images
(dim(meta_PUUM)-dim(unique_beetle))
table(unique_beetle$Species)  # Frequency table of species
dim(table(unique_beetle$Species))

#------------------------------------------------------------
# 4. Load and Clean BeetlePalooza Dataset
#------------------------------------------------------------

# Load BeetlePalooza metadata and clean it by removing rows with missing genus or species
meta_Plooza <- read.csv("./BeetlePalooza_Data/individual_metadata.csv")
head(meta_Plooza)  # View the first few rows of the BeetlePalooza metadata

# Filter out rows where genus or species are missing (NA or empty string)
meta_Plooza <- meta_Plooza %>%
  filter(!is.na(genus) & genus != "", !is.na(species) & species != "")

# Create a new column combining genus and species as a unique identifier
meta_Plooza$genus_spp <- paste0(meta_Plooza$genus, " ", meta_Plooza$species)

# Check species distribution in the BeetlePalooza dataset
dim(table(meta_Plooza$genus_spp))  # Output the count of unique genus and species combinations
table(meta_Plooza$genus_spp)  # Frequency table of genus_species combinations

#------------------------------------------------------------
# 5. Data Visualization: PUUM Beetle Species Abundance
#------------------------------------------------------------

# Sort species by their frequency in the unique beetle dataset for plotting
unique_beetle$scientificName <- factor(unique_beetle$scientificName, 
                                levels = names(sort(table(unique_beetle$scientificName), decreasing = FALSE)))

# Create a bar plot for species abundance in the PUUM dataset
png("./BeetlePUUM_abundance.png", width = 10, height = 5, units = "in", res = 300)  # Set output file and resolution
ggplot(data = unique_beetle, aes(x = scientificName)) +  # Create bar plot for scientificName (species)
  geom_bar() +  # Add bars for the count of each species
  geom_text(stat='count', aes(label = ..count..), hjust = -0.3, size = 3, angle = 90) +# Add count labels above the bars
  xlab("Species") +  # Label for x-axis
  ylab("Number of Individuals") +  # Label for y-axis
  theme_pubr() +  # Apply publication-style theme
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +  # Rotate x-axis labels
  scale_y_continuous(expand = expansion(mult = c(0, 0.05)))  # Adjust y-axis to remove gap below bars but keep space above
dev.off()  # Close the graphics device and save the plot

head(combined_data$individualID)
head(unique_beetle$BeetleID)
combined_data_merge<-merge(combined_data, unique_beetle, 
                           by.x = "individualID", by.y = "BeetleID", 
                           all = TRUE)
dim(combined_data)
dim(combined_data_merge)
table(combined_data_merge$SD.Card.Number)
combined_data_merge$imaged<-ifelse(combined_data_merge$SD.Card.Number==1, 
                                   paste0("Imaged"), paste0("Not Imaged"))
combined_data_merge$imaged[is.na(combined_data_merge$imaged)] <- "Not Imaged"

combined_data_merge$scientificName.x
combined_data_merge$scientificName.x[is.na(combined_data_merge$scientificName.x)] <- "Mecyclothorax gagnei"

combined_data_merge$scientificName.x <- factor(combined_data_merge$scientificName.x, 
                                       levels = names(sort(table(combined_data_merge$scientificName.x), decreasing = TRUE)))
combined_data_merge$imaged <- factor(combined_data_merge$imaged, 
                                               levels = c("Not Imaged","Imaged"))
# Summarize total counts per species for labeling
total_counts <- combined_data_merge %>%
  group_by(scientificName.x) %>%
  summarise(total = n(), .groups = "drop")

png("./BeetlePUUM_abundance.png", width = 6.5, height = 4, units = "in", res = 300)  # Set output file and resolution
ggplot(data = combined_data_merge, aes(x = scientificName.x, fill = imaged)) +
  geom_bar() +
  geom_text(data = total_counts, aes(x = scientificName.x, y = total, label = total),
            inherit.aes = FALSE, hjust = -0.3, size = 3) +
  xlab("Species") +
  ylab("Number of Pinned Individuals") +
  labs(fill = "Individual Imaging Status") +
  theme_pubr() +
  coord_flip() +
  scale_fill_manual(values = c("#cccccc", "#ba1419")) +
  theme(legend.position = c(0.7,0.3))+
#  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.3)))
dev.off()

#------------------------------------------------------------
# 6. Data Visualization: BeetlePalooza Species Abundance
#------------------------------------------------------------

# Load the beetle data from NEON API using the 'neonUtilities' package
NEON_df_2018 <- neonUtilities::loadByProduct(
  dpID = Beetle_dpID,  # Data product ID for beetles
  site = "all",  # Specify the site (PUUM is one of the NEON sites)
  startdate = "2018-01",
  enddate = "2018-12",
  token = NEON_TOKEN,  # API token for accessing the NEON data
  include.provisional = TRUE,  # Include provisional data (Must for PUUM)
  check.size = FALSE  # Do not check the file size
)

all<-NEON_df_2018$bet_sorting
table(all$sampleType)
all<-subset(all, sampleType=="carabid")
dim(table(all$scientificName))
dim(table(all$sampleID))



# Sort genus_species combinations by frequency in the BeetlePalooza dataset for plotting
meta_Plooza$genus_spp <- factor(meta_Plooza$genus_spp, 
                                levels = names(sort(table(meta_Plooza$genus_spp), decreasing = TRUE)))

dim(meta_Plooza)
dim(table(meta_Plooza$genus_spp))
dim(table(meta_Plooza$NEON_sampleID))

dim(table(meta_Plooza$genus))
sort(table(meta_Plooza$genus))

sum(sort(table(meta_Plooza$genus))[31:33])/nrow(meta_Plooza)


dim(table(meta_Plooza$genus_spp))/dim(table(all$scientificName))
dim(table(meta_Plooza$NEON_sampleID))/dim(table(all$sampleID))

# Create a bar plot for species abundance in the BeetlePalooza dataset
png("./BeetlePalooza_abundance.png", width = 10, height = 10, units = "in", res = 300)# Set output file and resolution
ggplot(data = meta_Plooza, aes(x = genus_spp)) +  # Create bar plot for genus_species (combined genus and species)
  geom_bar(fill="#ba1419") +  # Add bars for the count of each genus_species combination
  geom_text(stat='count', aes(label = ..count..), hjust = -0.3, size = 3) + # Add count labels above the bars
  xlab("Species") +  # Label for x-axis
  ylab("Number of Individuals") +  # Label for y-axis
  theme_pubr() +  # Apply publication-style theme
  coord_flip() +
  theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)) +  # Rotate x-axis labels
  scale_y_continuous(expand = expansion(mult = c(0, 0.05)))  # Adjust y-axis to remove gap below bars but keep space above
dev.off()  # Close the graphics device and save the plot


all$scientificName <- factor(all$scientificName,
                             levels = names(sort(table(all$scientificName), decreasing = TRUE)))
# binary “imaged” / “unimaged” flag based on whether the NEON species is in your BeetlePalooza list
all$spp_imaged <- ifelse(
  all$scientificName %in% meta_Plooza$genus_spp,
  "imaged",
  "unimaged"
)
# (optional) turn into a factor with a consistent ordering
all$spp_imaged <- factor(all$spp_imaged, levels = c("unimaged","imaged"))

png("./BeetlePalooza_NEON_abundance.png", width = 5, height = 4, units = "in", res = 300)# Set output file and resolution
ggplot(data = all, aes(x = scientificName, fill=spp_imaged)) +  # Create bar plot for genus_species (combined genus and species)
  geom_bar() +  # Add bars for the count of each genus_species combination
#  geom_text(stat='count', aes(label = ..count..), hjust = -0.3, size = 3) + # Add count labels above the bars
  xlab("Species (ordered by frequency of occurance)") +  # Label for x-axis
  ylab("Number of Vials") +  # Label for y-axis
  labs(fill = "Species Imaging Status") +
  scale_fill_manual(values = c("#cccccc", "#ba1419"), labels = c("No Vials Imaged","Some Vials Imaged")) +
  theme_pubr() +  # Apply publication-style theme
  coord_flip() +
  theme(axis.text.y  = element_blank(),  # remove the x-axis text
        axis.ticks.y = element_blank()) +   # (optional) remove the x-axis tick marks
  theme(legend.position = c(0.6, 0.25)) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05)))  # Adjust y-axis to remove gap below bars but keep space above
dev.off()

#------------------------------------------------------------
# 7. Generate Key for Image-Specific Species Data
#------------------------------------------------------------

# Create a key for the image-specific species data
img_spp_key <- meta_PUUM %>%
  group_by(ImageFileName) %>%  # Group by ImageFileName to get unique entries
  slice(1) %>%  # Keep only the first occurrence of each ImageFileName
  ungroup()  # Ungroup after processing

# Convert the key to a data frame and remove extra columns
img_spp_key<-as.data.frame(img_spp_key[,c("ImageFileName","Species")])
img_spp_key$file<-paste0("IMG_",substr(img_spp_key$ImageFileName, 5,nchar(img_spp_key$ImageFileName)),".JPG")

#Read in file with body sizes from annotations
body_size<-read.csv("./BeetlePUUM/Annotations/traits_metadata.csv")
head(body_size)
head(img_spp_key)
body_size$toras_path<-paste0(substr(body_size$ImageFilePath, 14, (nchar(body_size$ImageFilePath)-4)),".JPG")
body_size<-merge(body_size, img_spp_key, by.x = "toras_path", by.y = "file")
head(body_size)
table(body_size$cm_elytra_max_length)
body_size<-subset(body_size, cm_elytra_max_length>0)

species_counts <- table(body_size$Species)

legend_labels <- paste0(names(species_counts), " (n=", species_counts, ")")
names(legend_labels) <- names(species_counts)  # Assign species as names

png("./PUUM_bodysize_all.png", width = 12, height = 6, units = "in", res = 300)# Set output file and resolution
ggplot(data = body_size, aes(x = cm_elytra_max_length, fill = Species)) +
  geom_density(alpha = 0.5) +
  xlab("Elytra Length (cm)") +
  ylab("Density") + 
  scale_fill_discrete(labels = legend_labels, name = "Species (n)") +
  theme_pubr()
dev.off()


body_size$individualID<-paste0("NEON.",body_size$BeetleID)

body_size_NEON<-merge(body_size, combined_data, by="individualID", all.x = TRUE, all.y = FALSE)

body_size_NEON<-subset(body_size_NEON, plotID!="PUUM_016")

png("./PUUM_bodysize_all.png", width = 12, height = 6, units = "in", res = 300)# Set output file and resolution
ggplot(data = body_size_NEON, aes(x = cm_elytra_max_length, fill = scientificName)) +
  geom_density(alpha = 0.5) +
  xlab("Elytra Length (cm)") +
  ylab("Density") + 
  scale_fill_discrete(labels = legend_labels, name = "Species") +
  theme_pubr() +
  facet_wrap(.~plotID, nrow = 2, scales = "free_y")
dev.off()

density_plot<-ggplot(data = body_size_NEON, aes(x = cm_elytra_max_length, fill = scientificName)) +
  geom_histogram(alpha = 0.5, col="black") +
  scale_fill_discrete(labels = legend_labels, name = "Species") 

legend <- get_legend(density_plot)

library(grid)
library(gridExtra) 
png("./PUUM_bodysize_legend.png", width = 2.5, height = 4, units = "in", res = 300, bg = "transparent")# Set output file and resolution
grid.newpage()
grid.draw(legend)
dev.off()

png("./PUUM_bodysize_all_wrap_4.png", width = 9, height = 9, units = "in", res = 300)# Set output file and resolution
ggplot(data = body_size_NEON, aes(x = cm_elytra_max_length, fill = scientificName)) +
  geom_density(alpha = 0.5) +
  xlab("Elytra Length (cm)") +
  ylab("Density") + 
  scale_fill_discrete(labels = legend_labels, name = "Species") +
  theme_pubr() +
  facet_wrap(.~plotID, nrow = 3, scales = "free_y")
dev.off()

Plot_locations<-NEON_df$bet_fielddata[,c("plotID","decimalLatitude","decimalLongitude")]
Plot_locations<- Plot_locations %>%
  group_by(plotID) %>%  # Group by ImageFileName to get unique entries
  slice(1) %>%  # Keep only the first occurrence of each ImageFileName
  ungroup()  # Ungroup after processing
Plot_locations<-as.data.frame(Plot_locations)
Plot_locations<-Plot_locations[-c(10),]
Plot_locations

write.csv(Plot_locations, "./Plot_locations.csv")

# 2. Subset to species with >10 individuals
species_to_keep <- names(species_counts[species_counts > 10])
body_size_filtered <- body_size %>%
  filter(Species %in% species_to_keep)

# 3. Update counts and legend labels
filtered_counts <- table(body_size_filtered$Species)
legend_labels <- paste0(names(filtered_counts), " (n=", filtered_counts, ")")
names(legend_labels) <- names(filtered_counts)

# 4. Generate a color palette for the remaining species
n_species <- length(filtered_counts)
colors <- brewer.pal(n = max(3, min(n_species, 12)), name = "Set3")  # Adjust if n_species > 12
if (n_species > 12) {
  # Extend palette if needed
  colors <- colorRampPalette(brewer.pal(12, "Set3"))(n_species)
}
names(colors) <- names(filtered_counts)

body_size_filtered<-subset(body_size_filtered, length_cm>0)
body_size<-subset(body_size, length_cm>0)


# 5. Plot
png("./PUUM_bodysize.png", width = 12, height = 6, units = "in", res = 300)# Set output file and resolution
ggplot(data = body_size_filtered, aes(x = length_cm, fill = Species)) +
  geom_density(alpha = 0.5) +
  xlab("Elytra Length (cm)") +
  ylab("Density") +
  theme_pubr() +
  theme(legend.text = element_text(size = 9))
dev.off()


min(body_size$length_cm)
png("./PUUM_bodysize_all.png", width = 10, height = 10, units = "in", res = 300)# Set output file and resolution
ggplot(data = body_size, aes(x=length_cm, fill = Species)) +
  geom_density(alpha=0.5) +
  theme_pubr() +  # Apply publication-style theme
  xlab("Elytra Lenght") +  # Label for x-axis
  ylab("Density")   # Label for y-axis
dev.off()  
#merge sizes dataframe with the key for the associated species based on image

#------------------------------------------------------------
# 
#------------------------------------------------------------
head(meta_Plooza)
table(meta_Plooza$NEON_sampleID)
meta_Plooza$Site<-substr(meta_Plooza$NEON_sampleID, 1, 4)
meta_Plooza$Plot<-substr(meta_Plooza$NEON_sampleID, 6, 8)

url <- "https://data.neonscience.org/api/v0/sites"
library(jsonlite)
sites_json <- fromJSON(url)
sites_df <- sites_json$data
site_to_domain <- setNames(sites_df$domainName, sites_df$siteCode)

meta_Plooza$Domain<-site_to_domain[meta_Plooza$Site]
sort(table(meta_Plooza$Domain))
  
table(meta_Plooza$Site)
dim(table(meta_Plooza$Site))
table(meta_Plooza$Plot)

# Create a summary of the number of species and number of individuals at each site
site_summary <- meta_Plooza %>%
  group_by(Site) %>%  # Group data by Site
  summarise(
    num_species = n_distinct(genus_spp),  # Count the number of unique species (genus_spp)
    num_individuals = n()  # Count the total number of individuals (rows)
  )
site_summary<-as.data.frame(site_summary)
site_summary<-rbind(site_summary, c("PUUM", n_distinct(unique_beetle$Species), nrow(unique_beetle)))
tail(site_summary)

write.csv(site_summary, "./site_summary.csv")
