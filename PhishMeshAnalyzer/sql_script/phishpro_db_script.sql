-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema phishpro_db
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema phishpro_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `phishpro_db` DEFAULT CHARACTER SET latin1 ;
USE `phishpro_db` ;

-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_Domains`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_Domains` (
  `domain_id` INT(11) NOT NULL AUTO_INCREMENT,
  `domain_name` VARCHAR(200) NULL DEFAULT NULL,
  `trust_score` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`domain_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 3530
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_DomainCertificates`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_DomainCertificates` (
  `certificate_id` INT(11) NOT NULL AUTO_INCREMENT,
  `valid_after` DATETIME NULL DEFAULT NULL,
  `valid_before` DATETIME NULL DEFAULT NULL,
  `is_ca` INT(11) NULL DEFAULT NULL,
  `subject` VARCHAR(500) NULL DEFAULT NULL,
  `issuer` VARCHAR(500) NULL DEFAULT NULL,
  `subject_alt_names` VARCHAR(5000) NULL DEFAULT NULL,
  `domain_id` INT(11) NULL DEFAULT NULL,
  `is_valid` INT(11) NULL DEFAULT NULL,
  `comments` VARCHAR(500) NULL DEFAULT NULL,
  PRIMARY KEY (`certificate_id`),
  INDEX `domain_id` (`domain_id` ASC),
  CONSTRAINT `tbl_DomainCertificates_ibfk_1`
    FOREIGN KEY (`domain_id`)
    REFERENCES `phishpro_db`.`tbl_Domains` (`domain_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_DomainCertificatesValidity`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_DomainCertificatesValidity` (
  `certificate_status_id` INT(11) NOT NULL AUTO_INCREMENT,
  `domain_id` INT(11) NULL DEFAULT NULL,
  `is_valid` INT(11) NULL DEFAULT NULL,
  `comments` VARCHAR(500) NULL DEFAULT NULL,
  PRIMARY KEY (`certificate_status_id`),
  INDEX `domain_id` (`domain_id` ASC),
  CONSTRAINT `tbl_DomainCertificatesValidity_ibfk_1`
    FOREIGN KEY (`domain_id`)
    REFERENCES `phishpro_db`.`tbl_Domains` (`domain_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_DomainHostInfo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_DomainHostInfo` (
  `host_id` INT(11) NOT NULL AUTO_INCREMENT,
  `domain_id` INT(11) NULL DEFAULT NULL,
  `geo_loc_details` VARCHAR(3000) NULL DEFAULT NULL,
  `registered_domain` VARCHAR(500) NULL DEFAULT NULL,
  `detected_by_blacklists` VARCHAR(5000) NULL DEFAULT NULL,
  `blacklisted_count` INT(11) NULL DEFAULT NULL,
  `total_blacklists` INT(11) NULL DEFAULT NULL,
  `ip_addr` VARCHAR(20) NULL DEFAULT NULL,
  PRIMARY KEY (`host_id`),
  INDEX `domain_id` (`domain_id` ASC),
  CONSTRAINT `tbl_DomainHostInfo_ibfk_1`
    FOREIGN KEY (`domain_id`)
    REFERENCES `phishpro_db`.`tbl_Domains` (`domain_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_PhishTankLinks`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_PhishTankLinks` (
  `phish_tank_ref_id` INT(11) NOT NULL AUTO_INCREMENT,
  `phish_tank_url` VARCHAR(300) NULL DEFAULT NULL,
  `recorded_datetime` DATETIME NULL DEFAULT NULL,
  `verification_datetime` DATETIME NULL DEFAULT NULL,
  `target` VARCHAR(100) NULL DEFAULT NULL,
  `status` VARCHAR(100) NULL DEFAULT NULL,
  `is_analyzed` TINYINT(1) NULL DEFAULT NULL,
  PRIMARY KEY (`phish_tank_ref_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 7236145
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_Sites`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_Sites` (
  `site_id` INT(11) NOT NULL AUTO_INCREMENT,
  `site_url` VARCHAR(300) NULL DEFAULT NULL,
  `phish_tank_ref_id` INT(11) NULL DEFAULT NULL,
  `domain_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`site_id`),
  INDEX `phish_tank_ref_id` (`phish_tank_ref_id` ASC),
  INDEX `domain_id` (`domain_id` ASC),
  CONSTRAINT `tbl_Sites_ibfk_1`
    FOREIGN KEY (`phish_tank_ref_id`)
    REFERENCES `phishpro_db`.`tbl_PhishTankLinks` (`phish_tank_ref_id`),
  CONSTRAINT `tbl_Sites_ibfk_2`
    FOREIGN KEY (`domain_id`)
    REFERENCES `phishpro_db`.`tbl_Domains` (`domain_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 9931
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_Pages`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_Pages` (
  `page_id` INT(11) NOT NULL AUTO_INCREMENT,
  `page_url` VARCHAR(300) NULL DEFAULT NULL,
  `page_title` VARCHAR(100) NULL DEFAULT NULL,
  `site_id` INT(11) NULL DEFAULT NULL,
  `page_image_id` VARCHAR(50) NULL DEFAULT NULL,
  PRIMARY KEY (`page_id`),
  INDEX `site_id` (`site_id` ASC),
  CONSTRAINT `tbl_Pages_ibfk_1`
    FOREIGN KEY (`site_id`)
    REFERENCES `phishpro_db`.`tbl_Sites` (`site_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 7951
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_FieldCategory`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_FieldCategory` (
  `field_category_id` INT(11) NOT NULL AUTO_INCREMENT,
  `field_category_name` VARCHAR(30) NULL DEFAULT NULL,
  PRIMARY KEY (`field_category_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 41
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_Elements`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_Elements` (
  `element_id` INT(11) NOT NULL AUTO_INCREMENT,
  `element_name` VARCHAR(50) NULL DEFAULT NULL,
  `element_tag` VARCHAR(50) NULL DEFAULT NULL,
  `element_html_id` VARCHAR(50) NULL DEFAULT NULL,
  `element_parsed_text` VARCHAR(100) NULL DEFAULT NULL,
  `element_form` VARCHAR(20) NULL DEFAULT NULL,
  `element_value` VARCHAR(100) NULL DEFAULT NULL,
  `element_position` VARCHAR(50) NULL DEFAULT NULL,
  `element_parsed_method` VARCHAR(100) NULL DEFAULT NULL,
  `page_id` INT(11) NULL DEFAULT NULL,
  `field_category_id` INT(11) NULL DEFAULT NULL,
  `element_frame_index` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`element_id`),
  INDEX `page_id` (`page_id` ASC),
  INDEX `field_category_id` (`field_category_id` ASC),
  CONSTRAINT `tbl_Elements_ibfk_1`
    FOREIGN KEY (`page_id`)
    REFERENCES `phishpro_db`.`tbl_Pages` (`page_id`),
  CONSTRAINT `tbl_Elements_ibfk_2`
    FOREIGN KEY (`field_category_id`)
    REFERENCES `phishpro_db`.`tbl_FieldCategory` (`field_category_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 9021
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_FieldCategoryTrainingData`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_FieldCategoryTrainingData` (
  `data_id` INT(11) NOT NULL AUTO_INCREMENT,
  `field_category_id` INT(11) NULL DEFAULT NULL,
  `field_text` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`data_id`),
  INDEX `field_category_id` (`field_category_id` ASC),
  CONSTRAINT `tbl_FieldCategoryTrainingData_ibfk_1`
    FOREIGN KEY (`field_category_id`)
    REFERENCES `phishpro_db`.`tbl_FieldCategory` (`field_category_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 143
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_PageRequestInfo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_PageRequestInfo` (
  `request_id` INT(11) NOT NULL AUTO_INCREMENT,
  `request_url` VARCHAR(10000) NULL DEFAULT NULL,
  `request_domain` VARCHAR(100) NULL DEFAULT NULL,
  `request_method` VARCHAR(10) NULL DEFAULT NULL,
  `request_type` VARCHAR(15) NULL DEFAULT NULL,
  `page_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`request_id`),
  INDEX `page_id` (`page_id` ASC),
  CONSTRAINT `tbl_PageRequestInfo_ibfk_1`
    FOREIGN KEY (`page_id`)
    REFERENCES `phishpro_db`.`tbl_Pages` (`page_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 217014
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_PageResponseInfo`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_PageResponseInfo` (
  `response_id` INT(11) NOT NULL AUTO_INCREMENT,
  `response_url` VARCHAR(10000) NULL DEFAULT NULL,
  `response_file_path` VARCHAR(500) NULL DEFAULT NULL,
  `response_file_hash` VARCHAR(50) NULL DEFAULT NULL,
  `page_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`response_id`),
  INDEX `page_id` (`page_id` ASC),
  CONSTRAINT `tbl_PageResponseInfo_ibfk_1`
    FOREIGN KEY (`page_id`)
    REFERENCES `phishpro_db`.`tbl_Pages` (`page_id`))
ENGINE = InnoDB
AUTO_INCREMENT = 178102
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_PageStatus`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_PageStatus` (
  `page_status_id` INT(11) NOT NULL AUTO_INCREMENT,
  `download_date` DATE NULL DEFAULT NULL,
  `download_status` VARCHAR(100) NULL DEFAULT NULL,
  `page_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`page_status_id`),
  INDEX `page_id` (`page_id` ASC),
  CONSTRAINT `tbl_PageStatus_ibfk_1`
    FOREIGN KEY (`page_id`)
    REFERENCES `phishpro_db`.`tbl_Pages` (`page_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_SiteGroups`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_SiteGroups` (
  `site_group_id` INT(11) NOT NULL AUTO_INCREMENT,
  `site_group` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`site_group_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_SiteImages`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_SiteImages` (
  `site_image_id` INT(11) NOT NULL AUTO_INCREMENT,
  `site_group_id` INT(11) NULL DEFAULT NULL,
  `site_similar_to` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`site_image_id`),
  INDEX `site_group_id` (`site_group_id` ASC),
  CONSTRAINT `tbl_SiteImages_ibfk_1`
    FOREIGN KEY (`site_group_id`)
    REFERENCES `phishpro_db`.`tbl_SiteGroups` (`site_group_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_SiteStatus`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_SiteStatus` (
  `status_id` INT(11) NOT NULL AUTO_INCREMENT,
  `status` VARCHAR(100) NULL DEFAULT NULL,
  `phish_id` INT(11) NULL DEFAULT NULL,
  PRIMARY KEY (`status_id`),
  INDEX `phish_id` (`phish_id` ASC),
  CONSTRAINT `tbl_SiteStatus_ibfk_1`
    FOREIGN KEY (`phish_id`)
    REFERENCES `phishpro_db`.`tbl_PhishTankLinks` (`phish_tank_ref_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `phishpro_db`.`tbl_TargetSites`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `phishpro_db`.`tbl_TargetSites` (
  `target_site_id` INT(11) NOT NULL AUTO_INCREMENT,
  `target_site_name` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`target_site_id`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
