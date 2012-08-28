require 'rubygems'
require 'haml'
require 'builder/xchar'

gem "user-choices"
require "user-choices"

 class Shamus
  class ChoicesCommand < UserChoices::Command 
    include UserChoices

    def add_sources(builder)
      builder.add_source(EnvironmentSource, :with_prefix, "COLUMBO_")
      builder.add_source(YamlConfigFileSource, :from_complete_path, File.join(Object.const_defined?('RAILS_ROOT') ? RAILS_ROOT : Dir.pwd, 'config', 'columbo.yml'))
    end
    def add_choices(builder)
      builder.add_choice(:SCREENSHOTS, :type => %w(all_when_then explicit), :default => 'all_when_then')
    end

    def execute # :nodoc:
      #STDERR.puts @user_choices.inspect
      @user_choices
    end
  end
  Choices = ChoicesCommand.new.execute
  
  ScreenshotStep = /^the system takes a screenshot|I take a screenshot$/

  class ColumboError < StandardError
  end

  def self.cucumber_world
    @@cucumber_world
  end
  def self.cucumber_world=(world)
    @@cucumber_world=world
  end

  class Columbo
    attr_accessor :options

    ABSTRACT_TAG = "ABSTRACT" #:nodoc:

    TEMPLATE_DIR =  File.join(File.dirname(__FILE__), '..', '..', 'templates') #:nodoc:
    
    FEATURES_INDEX_TEMPLATE = "features_index.haml" #:nodoc:

    FEATURES_INDEX_NAME = "features.html" #:nodoc:

    SCENARIO_INDEX_TEMPLATE = "scenario_index.haml" #:nodoc:

    SCENARIO_OUTLINE_INDEX_TEMPLATE = "scenario_outline_index.haml" #:nodoc:

    SCENARIO_OUTLINE_EXAMPLE_TEMPLATE = "scenario_outline_example.haml" #:nodoc:

    SCENARIO_INDEX_NAME = "index.html" #:nodoc:

    SCREENSHOT_DIR = "." #:nodoc:

    EXAMPLE_DIR_NAME = "example_" #:nodoc:

    def self.path
      @@path
    end

    def initialize( step_mother, path, options )
      path ||= 'columbo'
      FileUtils.mkdir_p(path)
      @@path = path
      @all_releases = []
      @all_features = []
    end

    def before_feature(feature)
      @all_features << { :short_name => feature.short_name, :abstract_lines => [], :scenarios => [] }
      @current_feature = feature
    end

    def comment_line( comment_line )
      @all_features[ current_feature_index ][:abstract_lines] << comment_line.slice( /^# ?(.+)/, 1)
    end

    def after_feature_element( feature_element )

      add_release feature_element.source_tag_names

      tags = {}
      tags[:release] = feature_element.shamus_release
      tags[:feature_id] = feature_element.shamus_feature_id
      scenario = {
        :tags => tags,
        :name => sprintf( "%s: %s", feature_element.instance_variable_get("@keyword"), feature_element.name),
        :feature_id => feature_element.shamus_feature_id,
        :failed? =>
            if feature_element.failed?
              "ScenarioFailed"
            else
              ""
            end
      }

      add_feature_scenario scenario

    end

    def after_feature( feature )
      @current_feature = nil
    end

    private
    
    def snapshot_tag(dir, shamus_snapshot_filename)
      [[%w(.png .bmp .gif .jpg), proc{|f| %Q(<img src="#{f}">) }], [['.html'], proc{|f| %Q(<iframe src="#{f}" style="width: 100%;"></iframe>) }]].each do |(exts, tagproc)|
        exts.each do |ext|
          snapshot_path = File.join(SCREENSHOT_DIR, shamus_snapshot_filename + ext)
          if File.exists?(File.join(dir, snapshot_path))
            return tagproc.call(snapshot_path)
          end
        end
      end
      return nil
    end
    

    def add_release( source_tag_names )

      # join with previous release tags, eliminated the duplicates, returning
      # an array with the releases sans "@" tag prefix
      releases = source_tag_names.map do | tag |
        tag.slice(/^@(release\.*.*)/i, 1)
      end
      unless releases.empty?
        @all_releases = @all_releases | releases.compact!
      end
    end

    def add_feature_scenario( scenario)
      @all_features[ current_feature_index ][:scenarios] << scenario
    end

    def current_feature_index
      @all_features.length - 1
    end

    def template_file( haml_file_name )
      File.read(File.join(TEMPLATE_DIR, haml_file_name))
    end
    public
    def after_step(stepthing)
      case stepthing
      when ::Cucumber::Ast::Step
        # outline step; nothing invoked. do nothing - the AfterStep deals with outline steps on each row 
      when ::Cucumber::Ast::StepInvocation
        if stepthing.shamus_snapshot?
          step_invocation = stepthing # Cucumber::Ast::StepInvocation
          step = step_invocation.instance_eval{ @step } # Cucumber::Ast::Step
          scenario = step.instance_eval{ @feature_element } # Cucumber::Ast::Scenario
          screenshot_dir = File.join(Shamus::Columbo.path, scenario.shamus_feature_id, Shamus::Columbo::SCREENSHOT_DIR)
          output_dir_base = File.join(screenshot_dir, step_invocation.shamus_snapshot_filename)
          Shamus.try_snapshot(output_dir_base, Shamus.cucumber_world)
        end
      else
        # those should be the only two classes passed to #after_step, but check just in case. 
        raise "Expected Cucumber::Ast::Step or StepInvocation; got #{stepthing.class}"
      end
    end
  end
end
class ::Cucumber::Ast::OutlineTable::ExampleRow
  def shamus_snapshot_filename(index)
    "example_row_line_#{line}_step_num_#{index}"
  end
end
class ::Cucumber::Ast::StepInvocation
  # used by shamus to keep track of what steps have been run, since cucumber doesn't care to share this information 
  attr_accessor :seen_by_shamus

  def shamus_snapshot_filename
    "step_invocation_line_#{@step.line}"
  end
  def shamus_snapshot?
    case Shamus::Choices[:SCREENSHOTS]
    when 'explicit'
      name =~ Shamus::ScreenshotStep
    when 'all_when_then'
      non_and_keyword =~ /^(When|Then)/
    else
      raise ArgumentError, "unrecognized configuration option for columbo: SCREENSHOTS=#{Shamus::Choices[:SCREENSHOTS].inspect}"
    end
  end
  def non_and_keyword
    keyword=nil
    @step_collection.each do |step|
      if step.keyword !~ /^And/
        keyword = step.keyword
      end
      if step==self
        return keyword
      end
    end
    raise "internal error" # shouldn't get here 
  end
end
module Shamus::HasFeatureID
  def shamus_scenario_dir_name
    File.join(Shamus::Columbo.path, shamus_feature_id)
  end
  def shamus_feature_id
    shamus_only_tag_matching(/\A@(pb|ee)/i, :description => "a PB/EE number")
  end
  def shamus_release
    shamus_only_tag_matching(/\A@release/i, :description => "a release")
  end
  private
  # find a tag matching the given regexp. if there are none, raise an error. if there are 
  # multiple, raise an error. if there is one, return it. 
  #
  # pass the optional :description flag to make the error message informative. 
  #
  # returns the tag without its preceding @ sign. 
  def shamus_only_tag_matching(regexp, options={})
    options[:description] ||= regexp.inspect
    matches = source_tag_names.select{|tag| tag =~ regexp }
    case matches.size
    when 0
      raise "encauntered no tags that looked like #{options[:description]}! tags were #{source_tag_names.inspect}"
    when 1
      matches.first.sub(/\A@/,'')
    else
      raise "encountered multiple tags that look like #{options[:description]}! #{matches.inspect}"
    end
  end
end
[::Cucumber::Ast::ScenarioOutline, ::Cucumber::Ast::Scenario].each do |klass|
  klass.send(:include, Shamus::HasFeatureID)
end

class Shamus
  # takes a snapshot (either a screenshot or the current page html) to the given file path and basename. 
  # 
  # if taking a screenshot, this will append the appropriate image extension to the argument; if saving
  # html, will append '.html'. 
  #
  # returns the file used if a snapshot of some sort was taken; nil if not. 
  def self.try_snapshot(file_path_base, cucumber_world)
    require 'fileutils'
    FileUtils.mkdir_p(File.dirname(file_path_base))
    result=nil
    
    capybara_driver = Object.const_defined?('Capybara') && Capybara.respond_to?(:current_session) ? Capybara.current_session.driver : nil
    valve_browser = Object.const_defined?('Valve') ? Valve.browser : nil
    selenium_browser = cucumber_world.respond_to?(:selenium) ? (Shamus.cucumber_world.selenium rescue nil) : nil
    if capybara_driver
      if capybara_driver.class.name =~ /Vapir\z/ # test by name in case Capybara::Driver::Vapir isn't a defined const 
        browser = capybara_driver.browser(:launch => false)
        if browser
          result = vapir_screen_capture(browser, file_path_base)
        end
      elsif capybara_driver.browser.respond_to?(:save_screenshot)
        result=file_path_base+".png"
        capybara_driver.browser.save_screenshot(File.expand_path(result))
        #There were examples of this online as a way to also take SSs in IE.
        #File.open(File.expand_path(result), 'wb') do |f| 
        #  f.write(Base64.decode64(capybara_driver.browser.screenshot_as(:base64))) 
        #end 
      else
        result = dump_html(capybara_driver.source.to_s, file_path_base)
      end
    elsif selenium_browser
      result=file_path_base+".png"
      selenium_browser.capture_entire_page_screenshot(File.expand_path(result), "background=#FFFFFF")
    elsif cucumber_world.respond_to?(:response) || cucumber_world.respond_to?(:response_body) # webrat 
      response_body = (cucumber_world.response_body rescue nil) || (cucumber_world.response.body rescue nil)
      if response_body
        result=dump_html(response_body, file_path_base)
      end
    elsif valve_browser
      result = vapir_screen_capture(valve_browser, file_path_base)
    end
    result
  end
  
  def self.vapir_screen_capture(browser, file_path_base)
    format = browser.class.name =~ /::IE$/ ? 'bmp' : 'png'
    result = file_path_base+'.'+format
    browser.screen_capture(result)
    result
  end
  def self.dump_html(html, file_path_base)
    result = file_path_base+'.html'
    File.open(result, 'w') do |outfile|
      outfile.write(html.to_xs)
    end
    result
  end
end

# this takes a snapshot for an ExampleRow step 
AfterStep do |stepthing|
  case stepthing
  when ::Cucumber::Ast::OutlineTable::ExampleRow
    step_invocation=nil
    step_invocation_index=nil
    stepthing.instance_eval{@step_invocations}.to_a.each_with_index do |a_step_invocation, a_step_invocation_index|
      if !a_step_invocation.seen_by_shamus
        step_invocation=a_step_invocation
        step_invocation_index=a_step_invocation_index
        a_step_invocation.seen_by_shamus = true
        break
      end
    end
    if step_invocation.shamus_snapshot?
      screenshot_dir = File.join(stepthing.shamus_example_dir, Shamus::Columbo::SCREENSHOT_DIR)
      output_dir_base = File.join(screenshot_dir, stepthing.shamus_snapshot_filename(step_invocation_index))
      Shamus.try_snapshot(output_dir_base, self)
    end
  when ::Cucumber::Ast::Scenario
    # this is a non-outline step invocation - do nothing; the formatter's #after_step deals with this 
  when ::Cucumber::Ast::ScenarioOutline
    # this is a background do nothing
  else
    # don't think anything else gets passed to AfterStep, but catch this in case
    raise "Unexpected thing given to AfterStep: #{stepthing.class}"
  end
end

Before do
  Shamus.cucumber_world = self
end

