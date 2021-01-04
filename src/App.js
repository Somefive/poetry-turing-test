import './App.css';
import 'antd/dist/antd.css'
import { Input, message, Button, Radio } from 'antd'
import { UserOutlined, ArrowRightOutlined, RobotOutlined } from '@ant-design/icons'
import { Component } from 'react'
import _ from 'lodash'
import poetries from './poetries.json'

// import Swiper core and required components
import SwiperCore, { Navigation, Pagination, Scrollbar, A11y } from 'swiper'
import { Swiper, SwiperSlide } from 'swiper/react'

// Import Swiper styles
import 'swiper/swiper.scss';
import 'swiper/components/navigation/navigation.scss'
import 'swiper/components/pagination/pagination.scss'
import 'swiper/components/scrollbar/scrollbar.scss'

// install Swiper components
SwiperCore.use([Navigation, Pagination, Scrollbar, A11y]);

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
          mode: 'easy'
      }
      this.poetries = _.shuffle(poetries)
    }

    renderLogin() {
      // renderModeButton = (mode, color) => <Button onClick={() => this.setState({mode})}></Button>
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
          {/* <div className="mode-choice">
              <Button onClick>Easy</Button>
              <Button>Hard</Button>
              <Button>Lunatic</Button>
          </div> */}
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
        <SwiperSlide>
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
      const score = _.countBy(this.state.turingTests, t => t.answer_id === t.human_id).true
      this.setState({score, model: 'score-board'})
    }

    renderPoetryTuringTest() {
      const submittable = _.find(this.state.turingTests, t => t.answer_id < 0) === undefined
      return (
        <div className="turing-test">
          <Swiper
            spaceBetween={50}
            slidesPerView={1}
            // navigation
            pagination={{ clickable: true }}
            scrollbar={{ draggable: true }}
            onSlideChange={() => console.log('slide change')}
            onSwiper={(swiper) => console.log(swiper)}
          >
            {this.state.turingTests.map(poetryTest => this.renderPoetryTest(poetryTest))}
          </Swiper>
          <div className="submit-btn">
            <Button type="primary" shape="circle" icon={<RobotOutlined />} disabled={!submittable} onClick={() => this.submit()}/>
          </div>
        </div>
      )
    }

    render() {
        return (
            <div className="App">
              {this.state.model === 'login' && this.renderLogin()}
              {this.state.model === 'poetry-turing-test' && this.renderPoetryTuringTest()}
              {this.state.model === 'score-board' && this.renderScoreBoard()}
            </div>
        )
    }
}