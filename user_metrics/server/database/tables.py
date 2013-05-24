from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()


class User:
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(254))
    role = Column(String(50))

    def __init__(self, username, email, is_admin):
        self.username = username
        self.email = email
        self.is_admin = is_admin

    def __repr__(self):
        return '<Researcher("{0}","{1}", "{2}")>'.format(self.username, self.email, self.is_admin)
    
    
#CREATE  TABLE IF NOT EXISTS `umapi`.`user` (
  #`id` INT NOT NULL ,
  #`username` VARCHAR(45) NULL ,
  #`email` VARCHAR(255) NULL ,
  #`role` VARCHAR(45) NULL ,
  #PRIMARY KEY (`id`) ,
  #UNIQUE INDEX `email_UNIQUE` (`email` ASC) ,
  #UNIQUE INDEX `username_UNIQUE` (`username` ASC) )
#ENGINE = InnoDB;


#CREATE  TABLE IF NOT EXISTS `umapi`.`user` (
  #`id` INT NOT NULL ,
  #`username` VARCHAR(45) NULL ,
  #`email` VARCHAR(255) NULL ,
  #`role` VARCHAR(45) NULL ,
  #PRIMARY KEY (`id`) ,
  #UNIQUE INDEX `email_UNIQUE` (`email` ASC) ,
  #UNIQUE INDEX `username_UNIQUE` (`username` ASC) )
#ENGINE = InnoDB;


#CREATE  TABLE IF NOT EXISTS `umapi`.`job` (
  #`id` INT NOT NULL ,
  #`user_id` INT NOT NULL ,
  #`arguments` TEXT NULL ,
  #`parent_job_id` INT NULL ,
  #`classpath` VARCHAR(200) NOT NULL ,
  #PRIMARY KEY (`id`) ,
  #INDEX `fk_research_result_researcher_idx` (`user_id` ASC) ,
  #CONSTRAINT `fk_research_result_researcher`
    #FOREIGN KEY (`user_id` )
    #REFERENCES `umapi`.`user` (`id` )
    #ON DELETE NO ACTION
    #ON UPDATE NO ACTION)
#ENGINE = InnoDB;
