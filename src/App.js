import './App.css';
import 'antd/dist/antd.css'
import { Input, message, Button } from 'antd'
import { UserOutlined, ArrowRightOutlined, RobotOutlined } from '@ant-design/icons'
import { Component } from 'react'
import _ from 'lodash'
import poetries from './poetries.json'

// import Swiper core and required components
import SwiperCore, { Navigation, Pagination, Scrollbar, A11y, Autoplay } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

// Import Swiper styles
import 'swiper/swiper.scss';
import 'swiper/components/navigation/navigation.scss'
import 'swiper/components/pagination/pagination.scss'
import 'swiper/components/scrollbar/scrollbar.scss'

// install Swiper components
SwiperCore.use([Navigation, Pagination, Scrollbar, A11y, Autoplay]);

export default class App extends Component {
    constructor(props) {
      super(props)
      this.state = {
          model: 'login',
          username: '',
          score: 0,
          testSize: 5,
          testOffset: 0,
          turingTests: [],
          mode: 'easy',
          countDown: 0
      }
      this.poetries = _.shuffle(poetries)
      this.timer = undefined
      this.swiper = undefined
    }

    renderLogin() {
      const renderModeButton = (mode, color) => {
        return <Button onClick={() => this.setState({mode})} style={{
          color: mode === this.state.mode ? 'white' : 'black',
          background: mode === this.state.mode ? color : 'white',
          borderColor: color,
          borderRadius: 0,
          margin: '0.25em 0.75em'
        }}>{_.capitalize(mode)}</Button>
      }
      return (
        <div className="login">
          <div className="header">作诗图灵测试</div>
          <Input
            size="large"
            placeholder="请输入您的名字或昵称"
            prefix={<UserOutlined className="site-form-item-icon" />}
            suffix={
              <ArrowRightOutlined className="enter-btn" style={{color: this.state.username.length === 0 ? 'lightgray' : 'black'}} onClick={() => this.login()}/>
            }
            value={this.state.username}
            onChange={e => this.setState({username: e.target.value})}
            onPressEnter={() => this.login()}
          />
          <div className="mode-choice">
              {renderModeButton('easy', '#7cb305')}
              {renderModeButton('hard', '#cf1322')}
              {renderModeButton('lunatic', '#531dab')}
          </div>
          <div className="description">
            {this.state.mode === 'easy' && '在作诗图灵测试的Easy模式中，您将会被展现5组诗歌（包括标题、作者及内容），每组包括1首由诗人创作的诗歌和1首AI创作的诗歌，请选择您认为由人创作的诗歌。所有组选择完成后，您将会得知有多少组结果正确。'}
            {this.state.mode === 'hard' && '在作诗图灵测试的Hard模式中，您将会被展现10组诗歌（包括标题及内容），每组包括1首由诗人创作的诗歌和2首AI创作的诗歌，请选择您认为由人创作的诗歌，每组回答限时1分钟。所有组选择完成后，您将会得知有多少组结果正确。结果将被计入Hard模式排行榜。'}
            {this.state.mode === 'lunatic' && '在作诗图灵测试的Lunatic模式中，您将会被展现20组诗歌（仅包括诗歌内容），每组包括3首诗歌，其中至多包含1首由人创作的诗歌，请选择您认为由人创作的诗歌（若没有，则不选择），每组回答限时30秒。所有组选择完成后，您将会得知有多少组结果正确。结果将被计入Lunatic模式排行榜。'}
          </div>
        </div>
      )
    }

    login() {
      if (this.state.username.length === 0) message.warning('输入的名称不能为空')
      else {
        let tests = []
        for (let i = 0; i < this.state.testSize; ++i) {
          let poetry = this.poetries[(i + this.state.testOffset) % this.poetries.length]
          let ai_lines = _.shuffle(poetry['ai-lines'])[0]
          let is_first = _.random(0, 1) < 0.5
          tests.push({
            index: i,
            first: {
              id: 0,
              title: poetry.title,
              author: poetry.author,
              dynasty: poetry.dynasty,
              lines: is_first ? poetry.lines : ai_lines,
            },
            second: {
              id: 1,
              title: poetry.title,
              author: poetry.author,
              dynasty: poetry.dynasty,
              lines: is_first ? ai_lines : poetry.lines,
            },
            human_id: is_first ? 0 : 1,
            answer_id: -1,
          })
        }
        this.setState({model: 'poetry-turing-test', turingTests: tests})
      }
    }

    renderScoreBoard() {
      return (
        <div className="score-board">
          <div className="header">
            <div>{this.state.username}</div>
            <div>您的得分是：<span className="user-score">{this.state.score}</span> / {this.state.testSize}</div>
          </div>
          <div className="retry-btn"><Button size="large" onClick={() => this.setState({model: 'login', testOffset: this.state.testOffset + this.state.testSize})}>再来一次</Button></div>
        </div>
      )
    }

    renderPoetry(poetry, parent) {
      return (
        <div className={`poetry-card ${poetry.id === parent.answer_id ? 'selected': ''}`} onClick={() => {
          const tests = this.state.turingTests
          if (tests[parent.index].answer_id === poetry.id) tests[parent.index].answer_id = -1
          else tests[parent.index].answer_id = poetry.id
          this.setState({turingTests: tests})
        }}>
          <div className="poetry-card-inner">
            <div className="title">{poetry.title}</div>
            <div className="author">{poetry.dynasty && poetry.dynasty + ' '}{poetry.author}</div>
            {poetry.lines.map((line, idx) => <div className="line" idx={idx}>{line}</div>)}
          </div>
        </div>
      )
    }

    renderPoetryTest(poetryTest) {
      return (
        <SwiperSlide key={poetryTest.index}>
          <div className="poetry-container">
            <div className="poetry-inner">
              {this.renderPoetry(poetryTest.first, poetryTest)}
              {this.renderPoetry(poetryTest.second, poetryTest)}
            </div>
          </div>
        </SwiperSlide>
      )
    }

    submit() {
      const score = _.countBy(this.state.turingTests, t => t.answer_id === t.human_id).true || 0
      this.setState({score, model: 'score-board'})
    }

    onSlideChange(reset) {
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = undefined
      }
      if (this.state.mode !== 'easy') {
        if (reset) {
          this.setState({countDown: this.state.mode === 'hard' ? 60 : 30})
        }
        this.timer = setTimeout(() => {
          if (this.state.countDown === 1) {
            if (this.swiper) {
              if (this.swiper.realIndex === this.swiper.slides.length - 1) {
                this.submit()
              } else {
                this.swiper.slideNext()
              }
            }
          } else {
            this.setState({countDown: this.state.countDown - 1})
            this.onSlideChange(false)
          }
        }, 1000)
      }
    }

    renderPoetryTuringTest() {
      return (
        <div className="turing-test">
          <Swiper
            spaceBetween={50}
            slidesPerView={1}
            // navigation
            pagination={{ clickable: true }}
            scrollbar={{ draggable: true }}
            onSlideChange={() => this.onSlideChange(true)}
            onSwiper={(swiper) => {
              this.swiper = swiper
              this.onSlideChange(true)
            }}
            allowSlidePrev={this.state.mode === 'easy'}
          >
            {this.state.turingTests.map(poetryTest => this.renderPoetryTest(poetryTest))}
          </Swiper>
          <div className="submit-btn">
            <Button type="primary" shape="circle" icon={<RobotOutlined />} onClick={() => this.submit()}/>
          </div>
        </div>
      )
    }

    renderTimer() {
      return (
        <div className="timer">
          <Button style={{borderColor: this.state.countDown <= 10 ? 'red' : 'darkgray'}} type="default" shape="circle">{(this.state.countDown >= 10 ? "" : " ") + `${this.state.countDown}`}</Button>
        </div>
      )
    }

    render() {
        return (
          <div className="App">
            {this.state.model === 'login' && this.renderLogin()}
            {this.state.model === 'poetry-turing-test' && this.renderPoetryTuringTest()}
            {this.state.model === 'score-board' && this.renderScoreBoard()}
            {this.state.model === 'poetry-turing-test' && this.state.mode !== 'easy' && this.renderTimer()}
          </div>
        )
    }
}