from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

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


#-- -----------------------------------------------------
#-- Table `umapi`.`wiki_user`
#-- -----------------------------------------------------
#CREATE  TABLE IF NOT EXISTS `umapi`.`wiki_user` (
  #`id` INT NOT NULL ,
  #`mediawiki_user_name` VARCHAR(45) NULL ,
  #`mediawiki_user_id` INT NULL ,
  #`mediawiki_project` VARCHAR(45) NULL ,
  #PRIMARY KEY (`id`) )
#ENGINE = InnoDB;

class WikiUser:
    __tablename__ = 'wiki_user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    user_id = Column(Integer(50))
    project = Column(String(45))
    
    def __init__(self, username, user_id, project):
        """TODO: make this class accept either a username OR user_id"""
        self.username = username
        self.user_id = user_id
        self.project = project
    
    def __repr__(self):
        return '<WikiUser("{0}","{1}", "{2}")>'.format(self.username, self.user_id, self.project)

#-- -----------------------------------------------------
#-- Table `umapi`.`cohort_wiki_user`
#-- -----------------------------------------------------
#CREATE  TABLE IF NOT EXISTS `umapi`.`cohort_wiki_user` (
  #`id` INT NOT NULL ,
  #`wiki_user_id` INT NOT NULL ,
  #`cohort_id` INT NOT NULL ,
  #PRIMARY KEY (`id`) ,
  #INDEX `fk_cohort_wiki_user_wiki_user1` (`wiki_user_id` ASC) ,
  #INDEX `fk_cohort_wiki_user_cohort1` (`cohort_id` ASC) ,
  #CONSTRAINT `fk_cohort_wiki_user_wiki_user1`
    #FOREIGN KEY (`wiki_user_id` )
    #REFERENCES `umapi`.`wiki_user` (`id` )
    #ON DELETE NO ACTION
    #ON UPDATE NO ACTION,
  #CONSTRAINT `fk_cohort_wiki_user_cohort1`
    #FOREIGN KEY (`cohort_id` )
    #REFERENCES `umapi`.`cohort` (`id` )
    #ON DELETE NO ACTION
    #ON UPDATE NO ACTION)
#ENGINE = InnoDB;


class CohortWikiUser:
    __tablename__ = 'wiki_user'

    id = Column(Integer, primary_key=True)
    wiki_user_id = Column(Integer(50))
    cohort_id = Column(Integer(50))

    def __init__(self, wiki_user_id, cohort_id):
        self.wiki_user_id = wiki_user_id
        self.cohort_id = cohort_id

    def __repr__(self):
        return '<CohortWikiUser("{0}","{1}")>'.format(self.wiki_user_id, self.cohort_id)


# THIS SHOULD BE IN A SEPARATE FILE
# or rather the models should be in models.py

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    Base.metadata.create_all(bind=engine)
